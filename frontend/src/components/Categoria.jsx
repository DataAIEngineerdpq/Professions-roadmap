import { useState } from 'react';

/**
 * COMPONENTE: Categoria
 * =====================
 * Un componente es una función que devuelve interfaz. Este describe UNA
 * categoría del roadmap; React lo reutiliza para las 11 que tenés.
 *
 * Los valores entre llaves ({ nombre, niveles, ... }) son PROPS: los datos
 * que el componente padre le pasa. Son como los parámetros de una función.
 * Sin props, cada categoría tendría que escribirse a mano por separado.
 */

const NIVELES = ['Fundamento', 'Intermedio', 'Avanzado'];

function Categoria({ nombre, niveles, proporcion, total, busqueda, forzarAbierta }) {
  // useState es un HOOK: le da MEMORIA al componente.
  // 'abierta' guarda si esta categoría está desplegada; 'setAbierta' la cambia.
  // Sin estado, al hacer clic no pasaría nada: React no sabría que algo cambió
  // y no volvería a dibujar. Cada categoría tiene SU PROPIO estado independiente.
  const [abierta, setAbierta] = useState(false);

  // Si hay una búsqueda activa, la abrimos aunque el usuario no haya hecho clic.
  const estaAbierta = forzarAbierta ?? abierta;

  return (
    <section className="category">
      <button
        className="cat-header"
        onClick={() => setAbierta(!abierta)}
        aria-expanded={estaAbierta}
      >
        <svg
          className={`chevron ${estaAbierta ? 'open' : ''}`}
          width="11" height="11" viewBox="0 0 10 10" aria-hidden="true"
        >
          <path d="M3 1L7 5L3 9" fill="none" stroke="currentColor"
                strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
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
            {/* .map() convierte una lista de datos en una lista de elementos.
                Es el reemplazo de escribir cada nivel a mano. */}
            {NIVELES.map((nivel) => {
              const skills = niveles[nivel] || [];
              if (skills.length === 0) return null;

              return (
                <div className={`level level-${nivel.toLowerCase()}`} key={nivel}>
                  <div className="level-label">{nivel}</div>
                  <div className="skills">
                    {skills.map((skill) => {
                      const coincide =
                        busqueda && skill.toLowerCase().includes(busqueda.toLowerCase());
                      return (
                        // 'key' ayuda a React a identificar cada elemento de la
                        // lista. Sin key, React se confunde al actualizar y puede
                        // dibujar cosas en el lugar equivocado.
                        <span className={`skill ${coincide ? 'match' : ''}`} key={skill}>
                          {skill}
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
