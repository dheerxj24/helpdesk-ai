from app.database import SessionLocal
from app import models

db = SessionLocal()
db.query(models.ResolutionLog).delete()
db.query(models.Ticket).delete()
db.commit()
print("Cleared all tickets and resolution logs. KB articles untouched.")
db.close()