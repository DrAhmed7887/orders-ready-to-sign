-- Filtro básico de 1 variable, para comparar con las reglas: último FGe <60.
SELECT person_id FROM fge_ultimo WHERE valor < 60 ORDER BY person_id;
