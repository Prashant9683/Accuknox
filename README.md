# Accuknox

- Django Signals
- [Custom Classes](https://github.com/Prashant9683/Accuknox/blob/main/Custom%20Classes)

## Django Signals

**Question 1**
By default are django signals executed synchronously or asynchronously? Please support your answer with a code snippet that conclusively proves your stance. The code does not need to be elegant and production ready, we just need to understand your logic.

**Answer:**
By default, Django signals are synchronous. When a signal is emitted, the registered receiver functions are invoked directly on the same process path, and the code that emitted the signal will block to wait for all receiver functions to finish before proceeding.

```python
# models.py
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
import time
import datetime

class MyModel(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

@receiver(post_save, sender=MyModel)
def my_signal_handler(sender, instance, created, **kwargs):
    print(f"[{datetime.datetime.now()}] SIGNAL HANDLER: Starting handler for {instance.name}...")
    time.sleep(2) # Simulate a long-running task
    print(f"[{datetime.datetime.now()}] SIGNAL HANDLER: Finished handler for {instance.name}.")

# views.py/signals.py:
from .models import MyModel
import datetime

print(f"[{datetime.datetime.now()}] CALLER: About to save MyModel instance...")
my_instance = MyModel.objects.create(name="Test Signal Sync")
print(f"[{datetime.datetime.now()}] CALLER: Finished saving MyModel instance.")

# --- Expected Output ---
# [Timestamp] CALLER: About to save MyModel instance...
# [Timestamp] SIGNAL HANDLER: Starting handler for Test Signal Sync...
# (2 second delay here)
# [Timestamp + 2s] SIGNAL HANDLER: Finished handler for Test Signal Sync.
# [Timestamp + 2s] CALLER: Finished saving MyModel instance.

```

**Logic:** The output evidently indicates that the "CALLER: Finished saving." is printed only after the signal handler has finished executing (the time.sleep(2) too). This verifies that the signal blocks the caller, thus synchronous execution

**Question 2**
Do django signals run in the same thread as the caller? Please support your answer with a code snippet that conclusively proves your stance. The code does not need to be elegant and production ready, we just need to understand your logic.

**Answer:**
Yes, by default, Django signals run in the same thread as the caller.

```python
# models.py (MyModel from Q1)
from django.db.models.signals import post_save
from django.dispatch import receiver
import threading

# @receiver(post_save, sender=MyModel) # receiver decorator from Q1 is used
def my_signal_handler_thread_check(sender, instance, created, **kwargs):
    handler_thread_id = threading.current_thread().ident
    print(f"SIGNAL HANDLER: Running in thread ID: {handler_thread_id}")

# Connect the handler if not using decorator
# post_save.connect(my_signal_handler_thread_check, sender=MyModel)

# vies.py:
from .models import MyModel
import threading

caller_thread_id = threading.current_thread().ident
print(f"CALLER: Running in thread ID: {caller_thread_id}")
print("CALLER: About to save MyModel instance...")
my_instance = MyModel.objects.create(name="Test Signal Thread")
print("CALLER: Finished saving MyModel instance.")

# --- Expected Output ---
# CALLER: Running in thread ID: <THREAD_ID_X>
# CALLER: About to save MyModel instance...
# SIGNAL HANDLER: Running in thread ID: <THREAD_ID_X>
# CALLER: Finished saving MyModel instance.
```

**Logic:** The output will reveal the same thread ID printed by both the caller code (prior to saving the model) and the signal handler code. This is an affirmation that they run in the same thread.

**Question 3:**
By default do django signals run in the same database transaction as the caller? Please support your answer with a code snippet that conclusively proves your stance. The code does not need to be elegant and production ready, we just need to understand your logic.

**Answer:**
Yes, by default, Django signals run within the same database transaction as the code that triggered them (e.g., saving a model). If the transaction is rolled back, any database operations performed within the signal handler will be rolled back as well.

```python
# models.py (MyModel from Q1)
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction, DatabaseError

class LogEntry(models.Model):
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

# @receiver(post_save, sender=MyModel) #receiver decorator from Q1 is used
def my_signal_handler_transaction_check(sender, instance, created, **kwargs):
    print(f"SIGNAL HANDLER: Creating LogEntry for {instance.name}")
    try:
        LogEntry.objects.create(message=f"MyModel '{instance.name}' saved.")
        print("SIGNAL HANDLER: LogEntry created successfully (within transaction).")
    except DatabaseError as e:
         print(f"SIGNAL HANDLER: Failed to create LogEntry: {e}")


# Connect the handler if not using decorator
# post_save.connect(my_signal_handler_transaction_check, sender=MyModel)


# views.py:
from .models import MyModel, LogEntry
from django.db import transaction, DatabaseError

print(f"Before transaction: MyModel count={MyModel.objects.count()}, LogEntry count={LogEntry.objects.count()}")

try:
    with transaction.atomic():
        print("CALLER: Starting atomic transaction...")
        # This save triggers the signal
        instance = MyModel.objects.create(name="Test Transaction Success")
        print(f"CALLER: MyModel '{instance.name}' created within transaction.")
        # Simulate successful completion
        print("CALLER: Transaction will commit.")
except DatabaseError as e:
    print(f"CALLER: Transaction failed: {e}")

print(f"After successful transaction: MyModel count={MyModel.objects.count()}, LogEntry count={LogEntry.objects.count()}")
print("-" * 20)

# --- Test Case 2: Transaction Rollback ---
print(f"Before transaction rollback: MyModel count={MyModel.objects.count()}, LogEntry count={LogEntry.objects.count()}")
try:
    with transaction.atomic():
        print("CALLER: Starting atomic transaction for rollback test...")
        # This save triggers the signal
        instance = MyModel.objects.create(name="Test Transaction Rollback")
        print(f"CALLER: MyModel '{instance.name}' created within transaction.")
        # Force a rollback
        print("CALLER: Raising exception to force rollback...")
        raise ValueError("Simulating transaction failure")
except ValueError as e:
    print(f"CALLER: Caught expected exception: {e}. Transaction rolled back.")
except DatabaseError as e: # Catch potential DB errors too
    print(f"CALLER: Transaction failed with DB error: {e}")


print(f"After rolled-back transaction: MyModel count={MyModel.objects.count()}, LogEntry count={LogEntry.objects.count()}")


# --- Expected Output ---
# Before transaction: MyModel count=0, LogEntry count=0
# CALLER: Starting atomic transaction...
# SIGNAL HANDLER: Creating LogEntry for Test Transaction Success
# SIGNAL HANDLER: LogEntry created successfully (within transaction).
# CALLER: MyModel 'Test Transaction Success' created within transaction.
# CALLER: Transaction will commit.
# After successful transaction: MyModel count=1, LogEntry count=1
# --------------------
# Before transaction rollback: MyModel count=1, LogEntry count=1
# CALLER: Starting atomic transaction for rollback test...
# SIGNAL HANDLER: Creating LogEntry for Test Transaction Rollback
# SIGNAL HANDLER: LogEntry created successfully (within transaction).
# CALLER: MyModel 'Test Transaction Rollback' created within transaction.
# CALLER: Raising exception to force rollback...
# CALLER: Caught expected exception: Simulating transaction failure. Transaction rolled back.
# After rolled-back transaction: MyModel count=1, LogEntry count=1
```

**Logic:**

- In the first test case, the MyModel object is saved, triggering the signal to create a LogEntry. The transaction is properly committed. The MyModel object and the LogEntry are stored in the database, as seen by the fact that the counts are increased.
- In the second test case, the MyModel object is created, and the signal handler executes, creating a LogEntry within the same transaction. An exception is, however, raised after the signal handler has executed but before the transaction.atomic() block has finished. This causes a rollback.
- The final counts show that neither the MyModel instance ("Test Transaction Rollback") nor the corresponding LogEntry were committed to the database. This demonstrates that the database action of the signal handler (creating LogEntry) was part of the same transaction as creating MyModel and was successfully rolled back when the transaction was aborted.