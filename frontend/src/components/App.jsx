import { useState, useEffect } from 'react';
import Categoria from './components/Categoria';
import './index.css';

const NIVELES = ['Fundamento', 'Intermedio', 'Avanzado'];

/** Cuenta cuántas skills tiene una categoría, sumando sus tres niveles. */
function contarSkills(categoria) {
  return NIVELES.reduce((suma, nivel) => suma + (categoria[nivel] || []).length, 0);
}

function App() {
  const [datos, setDatos] = useState(null);
  const [error, setError] = useState(null);
  const [busqueda, setBusqueda] = useState('');
  // Qué rol está seleccionado. null = todavía no se cargaron los datos.
  const [rol, setRol] = useState(null);

  useEffect(() => {
    fetch('/roadmap_final.json')
      .then((r) => {
        if (!r.ok) throw new Error('No se encontró roadmap_final.json');
        return r.json();
      })
      .then((json) => {
        setDatos(json);
        // Arrancamos mostrando el rol con más ofertas: el más representativo.
        const roles = Object.keys(json).sort(
          (a, b) => json[b].total_ofertas - json[a].total_ofertas
        );
        setRol(roles[0]);
      })
      .catch((e) => setError(e.message));
  }, []);

  if (error) {
    return (
      <div className="app">
        <div className="state error">
          <p>{error}</p>
          <p>
            Copiá el archivo del pipeline:<br />
            <code>data/processed/roadmap_final.json</code> → <code>frontend/public/</code>
          </p>
        </div>
      </div>
    );
  }

  if (!datos || !rol) {
    return <div className="app"><div className="state">Cargando roadmap…</div></div>;
  }

  // Roles ordenados por cantidad de ofertas: los más relevantes primero.
  const roles = Object.keys(datos).sort(
    (a, b) => datos[b].total_ofertas - datos[a].total_ofertas
  );

  const rolActual = datos[rol];
  const arbol = rolActual.categorias;

  const categorias = Object.keys(arbol).sort(
    (a, b) => contarSkills(arbol[b]) - contarSkills(arbol[a])
  );
  const totalSkills = categorias.reduce((s, c) => s + contarSkills(arbol[c]), 0);

  // La demanda más alta del rol: sirve de referencia para la intensidad de color.
  const maxDemanda = Math.max(
    1,
    ...categorias.flatMap((c) =>
      NIVELES.flatMap((n) => (arbol[c][n] || []).map((s) => s.demanda))
    )
  );

  const termino = busqueda.trim().toLowerCase();
  const visibles = termino
    ? categorias.filter((cat) =>
        NIVELES.some((n) =>
          (arbol[cat][n] || []).some((s) => s.nombre.toLowerCase().includes(termino))
        )
      )
    : categorias;

  return (
    <div className="app">
      <header className="header">
        <p className="eyebrow">Extraído de ofertas reales</p>
        <h1 className="title">Roadmap de Skills</h1>
        <p className="tagline">
          Lo que las empresas piden hoy, tomado directamente de sus ofertas de empleo.
          El número junto a cada skill es en cuántas ofertas aparece.
        </p>

        <div className="stats">
          <div>
            <div className="stat-value">{totalSkills}</div>
            <div className="stat-label">Skills</div>
          </div>
          <div>
            <div className="stat-value">{rolActual.total_ofertas}</div>
            <div className="stat-label">Ofertas</div>
          </div>
          <div>
            <div className="stat-value">{categorias.length}</div>
            <div className="stat-label">Categorías</div>
          </div>
        </div>
      </header>

      {/* Selector de rol: cada botón cambia el roadmap completo */}
      <nav className="roles" aria-label="Elegir rol">
        {roles.map((r) => (
          <button
            key={r}
            className={`role-btn ${r === rol ? 'active' : ''}`}
            onClick={() => setRol(r)}
            aria-pressed={r === rol}
          >
            {r}
            <span className="role-count">{datos[r].total_ofertas}</span>
          </button>
        ))}
      </nav>

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
              key={`${rol}-${cat}`}
              nombre={cat}
              niveles={arbol[cat]}
              total={contarSkills(arbol[cat])}
              proporcion={Math.round((contarSkills(arbol[cat]) / totalSkills) * 100)}
              busqueda={termino}
              maxDemanda={maxDemanda}
              forzarAbierta={termino ? true : undefined}
            />
          ))
        )}
      </main>

      <div className="legend">
        <span><i className="legend-dot" style={{ background: 'var(--accent)' }} />Fundamento</span>
        <span><i className="legend-dot" style={{ background: 'var(--accent-2)' }} />Intermedio</span>
        <span><i className="legend-dot" style={{ background: 'var(--warn)' }} />Avanzado</span>
        <span className="legend-note">La intensidad indica cuánto se pide</span>
      </div>
    </div>
  );
}

export default App;
