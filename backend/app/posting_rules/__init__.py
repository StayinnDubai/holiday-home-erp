"""Maps operational events to journal entries.

Convention: one function per source event, named `post_<event>(db, <record>) -> JournalEntry`.
Each function is called by its owning service inside the same DB transaction as the
operational write it accounts for (see app/services/README or the plan §4 "Auto-posting").

Empty in the Foundation milestone — populated starting with the Accounting-core milestone,
once Bills/Reservations/Cheques exist to post from.
"""
