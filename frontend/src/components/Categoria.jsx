import { useState } from 'react';

const NIVELES = ['Fundamento', 'Intermedio', 'Avanzado'];

/**
 * Calcula la intensidad visual de una skill según su demanda.
 * Devuelve un valor entre 0.3 y 1: las más pedidas se ven fuertes,
 * las raras quedan tenues. Así la jerarquía se percibe de un vistazo,
 * sin tener que leer cada número.
 */
function intensidad(demanda, maxDemanda) {
  if (!maxDemanda) return 1;
  return 0.3 + (demanda / maxDemanda) * 0.7;
}

function Categoria({ nombre, niveles, total, proporcion, busqueda, maxDemanda, forzarAbierta }) {
  const [abierta, setAbierta] = useState(false);
  const estaAbierta = forzarAbierta ?? abierta;

  return (
    <section className="category">
      <button className="cat-header" onClick={() => setAbierta(!abierta)} aria-expanded={estaAbierta}>
        <svg className={`chevron ${estaAbierta ? 'open' : ''}`} width="11" height="11" viewBox="0 0 10 10" aria-hidden="true">
          <path d="M3 1L7 5L3 9" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <span className="cat-name">{nombre}</span>
        <span className="cat-count">{total}</span>
      </button>

      <div className="share-bar">
        <div className="share-fill" style={{ width: `${proporcion}%` }} />
      </div>

      <div className={`cat-body ${estaAbierta ? 'open' : ''}`}>
        <div>
          <div className="levels">
            {NIVELES.map((nivel) => {
              const skills = niveles[nivel] || [];
              if (skills.length === 0) return null;

              return (
                <div className={`level level-${nivel.toLowerCase()}`} key={nivel}>
                  <div className="level-label">{nivel}</div>
                  <div className="skills">
                    {skills.map((skill) => {
                      const coincide = busqueda && skill.nombre.toLowerCase().includes(busqueda);
                      return (
                        <span
                          className={`skill ${coincide ? 'match' : ''}`}
                          key={skill.nombre}
                          style={{ opacity: coincide ? 1 : intensidad(skill.demanda, maxDemanda) }}
                          title={`Aparece en ${skill.demanda} oferta${skill.demanda === 1 ? '' : 's'}`}
                        >
                          {skill.nombre}
                          <b className="skill-demand">{skill.demanda}</b>
                        </span>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}

export default Categoria;
