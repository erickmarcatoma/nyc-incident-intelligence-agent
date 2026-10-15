export default function AgentInput({
  borough,
  boroughs,
  question,
  loading,
  onBoroughChange,
  onQuestionChange,
  onSubmit,
}) {
  const examples = [
    "Which recent crashes reported injuries?",
    "Summarize the latest collision reports.",
    "What patterns appear in these records?",
  ];

  return (
    <form className="briefing-form" onSubmit={onSubmit}>
      <div className="form-topline">
        <label className="field-label" htmlFor="borough">
          BOROUGH
        </label>
        <span className="field-hint">Choose an area to explore</span>
      </div>
      <div className="borough-options" role="group" aria-label="Choose a borough">
        {boroughs.map((name) => (
          <button
            className={`borough-option${borough === name ? " is-selected" : ""}`}
            type="button"
            key={name}
            aria-pressed={borough === name}
            onClick={() => onBoroughChange(name)}
          >
            {name}
          </button>
        ))}
      </div>

      <label className="field-label question-label" htmlFor="question">
        YOUR QUESTION
      </label>
      <div className="question-box">
        <textarea
          id="question"
          name="question"
          rows="3"
          maxLength="500"
          required
          value={question}
          onChange={(event) => onQuestionChange(event.target.value)}
          placeholder={`Ask about collision reports in ${borough}…`}
        />
        <div className="question-footer">
          <span>Claude answers using the returned dataset records.</span>
          <span>{question.length}/500</span>
        </div>
      </div>

      <div className="form-actions">
        <button className="submit-button" type="submit" disabled={loading}>
          {loading ? (
            <>
              <span className="button-spinner" />
              Analyzing…
            </>
          ) : (
            <>
              Get briefing <span aria-hidden="true">↗</span>
            </>
          )}
        </button>
        <span className="form-assurance">
          <span aria-hidden="true">⌁</span> Your API key stays on the server
        </span>
      </div>

      <div className="example-prompts">
        <span>TRY ASKING</span>
        {examples.map((example) => (
          <button
            type="button"
            key={example}
            onClick={() =>
              onQuestionChange(
                `${example.replace(/\.$/, "")} in ${borough}.`,
              )
            }
          >
            {example}
          </button>
        ))}
      </div>
    </form>
  );
}