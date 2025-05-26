-- Create the optional_conditions table if it doesn't exist
create table if not exists optional_conditions (
    id serial primary key,
    description text not null,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Insert some sample optional conditions
insert into optional_conditions (description) values
    ('Demostró empatía excepcional al abordar las preocupaciones del cliente'),
    ('Proporcionó ejemplos específicos y relevantes de casos de uso'),
    ('Hizo preguntas de seguimiento perspicaces para entender mejor las necesidades'),
    ('Explicó conceptos técnicos de manera clara y accesible'),
    ('Manejó objeciones de manera proactiva y constructiva'),
    ('Conectó las características del producto con beneficios comerciales específicos'),
    ('Demostró conocimiento profundo del sector o industria del cliente'),
    ('Ofreció soluciones personalizadas basadas en las necesidades específicas'),
    ('Utilizó un lenguaje positivo y orientado a soluciones'),
    ('Mantuvo un tono profesional y respetuoso durante toda la conversación')
on conflict (id) do nothing; 