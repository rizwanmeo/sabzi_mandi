@echo off
For /f "tokens=1,2,3,4,5 delims=/. " %%a in ('date/T') do set CDate=E:\backup\%%a-%%b-%%c.sql
cd "c:\Program Files\PostgreSQL\10\bin"
pg_dump.exe --dbname=postgresql://postgres:postgres@127.0.0.1:5432/sabzi_mandi > %CDate%
pause
