@echo off
chcp 65001 >nul
cd /d "%~dp0..\.."
set OUT=reports\agy\probe.txt
echo === where agy === > %OUT%
where agy >> %OUT% 2>&1
echo === agy --version === >> %OUT%
call agy --version >> %OUT% 2>&1
echo === agy --help === >> %OUT%
call agy --help >> %OUT% 2>&1
echo === agy models --help === >> %OUT%
call agy models --help >> %OUT% 2>&1
echo === agy models list === >> %OUT%
call agy models list >> %OUT% 2>&1
echo === psql / node / python === >> %OUT%
where psql node npm python >> %OUT% 2>&1
call node --version >> %OUT% 2>&1
call python --version >> %OUT% 2>&1
call psql --version >> %OUT% 2>&1
echo === DONE === >> %OUT%
