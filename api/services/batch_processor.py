"""
api/services/batch_processor.py
----------------------------------
Handles processing a big CSV of customers WITHOUT freezing the API while
it works. This function will be handed off to FastAPI's BackgroundTasks,
which runs it "after" the response has already been sent back to the
client.

TIMELINE OF WHAT HAPPENS:
1. Client uploads a CSV with, say, 500 customers
2. We immediately create a "batch" database row with status="processing"
   and respond to the client right away: "Got it, batch_id=7, check back"
3. THIS function then runs in the background, row by row, saving
   predictions as it goes
4. Client can call GET /batch-status/7 anytime to check progress
5. Once done, we mark the batch status="completed"

This is exactly the "smart waiter" pattern from earlier: the client isn't
stuck waiting for all 500 predictions before getting ANY response.
"""

import os
import pandas as pd
from sqlalchemy.orm import Session
from api.db import models
from api.services.predictor import predictor
from api.services.cache import get_cached_prediction, set_cached_prediction
from api.services.logger import get_logger

logger = get_logger(__name__)


def process_batch(batch_id: int, csv_path: str, owner_id: int, db_session_factory):
    """
    db_session_factory: we pass in SessionLocal (not a session itself),
    because this function runs in the background, separate from the
    original request's database session, which may already be closed by
    the time this runs. We open our OWN fresh session here instead.
    """
    db: Session = db_session_factory()
    try:
        batch = db.query(models.PredictionBatch).filter(models.PredictionBatch.id == batch_id).first()

        df = pd.read_csv(csv_path)
        batch.total_rows = len(df)
        db.commit()
        logger.info(f"batch_id={batch_id} status=STARTED total_rows={len(df)}")

        for _, row in df.iterrows():
            customer = row.to_dict()

            # A single malformed row (bad category, corrupted value, a
            # column we don't recognize) should NOT take down the entire
            # batch. We isolate each row's processing so one failure just
            # gets logged and skipped, and everything else still completes.
            try:
                # Check the cache first - if we've seen this exact profile
                # recently, skip re-running the model entirely
                cached_result = get_cached_prediction(customer)
                if cached_result:
                    result = cached_result
                    from_cache = "yes"
                else:
                    result = predictor.predict(customer)
                    set_cached_prediction(customer, result)
                    from_cache = "no"

                record = models.PredictionRecord(
                    owner_id=owner_id,
                    batch_id=batch.id,
                    contract=customer.get("Contract"),
                    tenure=customer.get("tenure"),
                    monthly_charges=customer.get("MonthlyCharges"),
                    churn_probability=result["churn_probability"],
                    risk_level=result["risk_level"],
                    from_cache=from_cache,
                )
                db.add(record)
                batch.processed_rows += 1

            except Exception as row_error:
                # Log it and move on - don't let one bad row kill 7000 good ones
                batch.failed_rows += 1
                logger.warning(f"batch_id={batch_id} row_skipped error={row_error}")

            db.commit()  # commit progress incrementally so status polling sees live updates

        batch.status = "completed"
        from sqlalchemy.sql import func
        batch.completed_at = func.now()
        db.commit()
        logger.info(f"batch_id={batch_id} status=COMPLETED processed={batch.processed_rows} failed={batch.failed_rows}")

    except Exception as e:
        batch.status = "failed"
        batch.error_message = str(e)
        db.commit()
        logger.error(f"batch_id={batch_id} status=FAILED error={str(e)}")
    finally:
        db.close()
        # Clean up the temp file now that we're done with it, whether
        # processing succeeded or failed - otherwise every single upload
        # leaves a leftover file on disk forever, which would slowly fill
        # up the server's storage over time.
        if os.path.exists(csv_path):
            os.remove(csv_path)
