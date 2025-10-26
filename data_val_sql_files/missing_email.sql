-- missing email
select count(*)
from app_user 
where email is null;