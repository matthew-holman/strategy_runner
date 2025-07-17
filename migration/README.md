### Migrations
1. Make necessary changes in your DB classes
2. Update the imports in `create_tables` script to import the updated DB classes
3. Drop the existing tables from the DB instance running in your local
4. Run `create_tables::main` function
5. Check the latest status of the table matches with the changes you made in DB classes
6. Run Alembic (in the same directory where you have alembic.ini file) to automatically create revision scripts using table schemas defined on your local DB.
e.g. `alembic revision --autogenerate -m "Added a new column for alerts closed"`
7. Make the necessary changes in the generated migration script (make sure there are no table drop actions left)
8. Stop the docker compose services and remove them `docker-compose down && docker-compose rm -f`
9. Restart docker-compose and check the plm_api_dev_web logs to see if the latest migration could be applied without an error
10. Check the DB manually to see if the changes are there.
11. Commit and push the changes with a PR
