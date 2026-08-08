## EffortList

A website I made for bulk ordering stuff. Insert words and search them by prefix with autocomplete. you can use it however you want.

Supports batch-inserting words with .csv files, and you can specify which column to parse. Save your word entries by registering an account. All previously inserted words as a guest will be carried over  to the new account once created.

### Tests

The C and Python suites are kept separate and can be run independently:

```bash
make test-c
make test-python
```

Run both suites with:

```bash
make test
```

Python integration tests use a fresh temporary SQLite database for each test and
never read from or write to the development `entries.db`.


