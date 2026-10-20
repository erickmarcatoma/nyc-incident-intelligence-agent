export default function BoroughSelector({ boroughs, value, onChange }) {
  return (
    <nav className="borough-tabs" aria-label="Choose a borough">
      {boroughs.map((name) => (
        <button
          key={name}
          type="button"
          className={`borough-tab${value === name ? " is-selected" : ""}`}
          aria-pressed={value === name}
          onClick={() => onChange(name)}
        >
          {name}
        </button>
      ))}
    </nav>
  );
}
