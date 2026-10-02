from django.db import migrations

SQL = """
CREATE FUNCTION ardur_raw_inmutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'Los registros RAW son inmutables';
END;
$$;
CREATE TRIGGER ardur_raw_guard BEFORE UPDATE OR DELETE ON financiera_registrocarteraraw
FOR EACH ROW EXECUTE FUNCTION ardur_raw_inmutable();
"""

class Migration(migrations.Migration):
    dependencies = [('financiera', '0001_initial')]
    operations = [migrations.RunSQL(SQL, 'DROP TRIGGER ardur_raw_guard ON financiera_registrocarteraraw; DROP FUNCTION ardur_raw_inmutable();')]
