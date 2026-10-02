from django.db import migrations

SQL = """
CREATE FUNCTION ardur_auditoria_inmutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'Los eventos de auditoría son inmutables';
END;
$$;
CREATE TRIGGER ardur_auditoria_guard BEFORE UPDATE OR DELETE ON auditoria_eventoauditoria
FOR EACH ROW EXECUTE FUNCTION ardur_auditoria_inmutable();
"""

class Migration(migrations.Migration):
    dependencies = [('auditoria', '0001_initial')]
    operations = [migrations.RunSQL(SQL, 'DROP TRIGGER ardur_auditoria_guard ON auditoria_eventoauditoria; DROP FUNCTION ardur_auditoria_inmutable();')]
