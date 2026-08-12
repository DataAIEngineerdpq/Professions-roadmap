import { useState, useEffect } from 'react';
import Categoria from './components/Categoria';
import './index.css';

const NIVELES = ['Fundamento', 'Intermedio', 'Avanzado'];

/** Cuenta cuántas skills tiene una categoría, sumando sus tres niveles. */
function contarSkills(categoria) {
  return NIVELES.reduce((suma, nivel) => suma + (categoria[nivel] || []).length, 0);
}

function App() {
  // Tres piezas de estado, cada una con su responsabilidad:
  const [arbol, setArbol] = useState(null);        // los datos cargados
  const [error, setError] = useState(null);        // si la carga falló
  const [busqueda, setBusqueda] = useState('');    // lo que el usuario escribe

  // useEffect ejecuta código DESPUÉS de que el componente se dibuja.
  // Acá lo usamos para cargar el JSON. El array vacío [] al final significa
  // "corré esto UNA sola vez, al montar". Sin ese array, se ejecutaría en cada
  // redibujado y entraría en un bucle infinito de peticiones.
  useEffect(() => {
    fetch('/roadmap_tree.json')
      .then((respuesta) => {
        if (!respuesta.ok) throw new Error('No se encontró roadmap_tree.json');
        return respuesta.json();
      })
      .then(setArbol)
      .catch((e) => setError(e.message));
  }, []);

  if (error) {
    return (
      <div className="app">
        <div className="state error">
          <p>{error}</p>
          <p>
            Copiá el archivo del pipeline a la carpeta pública:<br />
            <code>data/processed/roadmap_tree.json</code> →{' '}
            <code>frontend/public/roadmap_tree.json</code>
          </p>
        </div>
      </div>
    );
  }

  if (!arbol) {
    return <div className="app"><div className="state">Cargando roadmap…</div></div>;
  }

  // Ordenamos las categorías por cantidad de skills: lo más demandado arriba.
  const categorias = Object.keys(arbol).sort(
    (a, b) => contarSkills(arbol[b]) - contarSkills(arbol[a])
  );
  const totalSkills = categorias.reduce((s, c) => s + contarSkills(arbol[c]), 0);

  // Si hay búsqueda, mostramos solo las categorías que tienen coincidencias.
  const termino = busqueda.trim().toLowerCase();
  const visibles = termino
    ? categorias.filter((cat) =>
        NIVELES.some((n) =>
          (arbol[cat][n] || []).some((s) => s.toLowerCase().includes(termino))
        )
      )
    : categorias;

  return (
    <div className="app">
      <header className="header">
        <p className="eyebrow">Extraído de ofertas reales</p>
        <h1 className="title">Roadmap de Skills</h1>
        <p className="tagline">
          Lo que las empresas piden hoy, tomado directamente de sus ofertas de
          empleo y organizado por categoría y nivel.
        </p>

        <div className="stats">
          <div>
            <div className="stat-value">{totalSkills}</div>
            <div className="stat-label">Skills</div>
          </div>
          <div>
            <div className="stat-value">{categorias.length}</div>
            <div className="stat-label">Categorías</div>
          </div>
        </div>
      </header>

      <div className="toolbar">
        <input
          className="search"
          type="search"
          placeholder="Buscar una skill…"
          value={busqueda}
          onChange={(e) => setBusqueda(e.target.value)}
          aria-label="Buscar skill"
        />
      </div>

      <main>
        {visibles.length === 0 ? (
          <div className="state">Ninguna skill coincide con «{busqueda}».</div>
        ) : (
          visibles.map((cat) => (
            <Categoria
              key={cat}
              nombre={cat}
              niveles={arbol[cat]}
              total={contarSkills(arbol[cat])}
              proporcion={Math.round((contarSkills(arbol[cat]) / totalSkills) * 100)}
              busqueda={termino}
              forzarAbierta={termino ? true : undefined}
            />
          ))
        )}
      </main>

      <div className="legend">
        <span><i className="legend-dot" style={{ background: 'var(--accent)' }} />Fundamento</span>
        <span><i className="legend-dot" style={{ background: 'var(--accent-2)' }} />Intermedio</span>
        <span><i className="legend-dot" style={{ background: 'var(--warn)' }} />Avanzado</span>
      </div>
    </div>
  );
}

export default App;
