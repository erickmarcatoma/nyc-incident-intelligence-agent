export default function AgentInput({ borough, question, loading, onQuestionChange, onSubmit }) {
  return (
    <form className="search-bar" onSubmit={onSubmit} role="search">
      <svg className="search-icon" viewBox="0 0 24 24" aria-hidden="true">
        <circle cx="11" cy="11" r="7" />
        <path d="m20 20-3.5-3.5" />
      </svg>
      <label className="visually-hidden" htmlFor="question">
        Ask about collision reports in {borough}
      </label>
      <input
        id="question"
        name="question"
        type="text"
        maxLength={500}
        required
        autoComplete="off"
        value={question}
        onChange={(event) => onQuestionChange(event.target.value)}
        placeholder={`What collisions were reported in ${borough}?`}
      />
      <button className="search-submit" type="submit" disabled={loading} aria-label="Get briefing">
        {loading ? (
          <span className="button-spinner" />
        ) : (
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M3 11.5 21 3l-8.5 18-2-7.5L3 11.5Z" />
          </svg>
        )}
      </button>
    </form>
  );
}
