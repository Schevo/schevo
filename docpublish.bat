REM winscp3.exe orbtech.com /synchronize doc/html /var/www/orbtech/orbtech.com/html/

REM winscp3.exe orbtech.com /command synchronize remote doc/html /var/www/orbtech/orbtech.com/html/ 

winscp3 /console /script=docpublish.txt

pause
