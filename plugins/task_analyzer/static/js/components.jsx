/** @jsx React.createElement */
// React components for Task Analyzer

const SafeMarkdown = ({ text, style }) => {
    const ref = React.useRef(null);
    React.useEffect(() => {
        if (ref.current) {
            ref.current.innerHTML = renderMarkdown(text);
        }
    }, [text]);
    return <div ref={ref} style={style} />;
};

const AnalysisMetrics = ({ analysisResult, showPrompt, setShowPrompt }) => (
    <div style={{
        marginBottom: '15px',
        padding: '12px',
        backgroundColor: '#0d1117',
        border: '1px solid #30363d',
        borderRadius: '6px'
    }}>
        <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '10px'
        }}>
            <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '20px',
                fontSize: '13px',
                color: '#8b949e'
            }}>
                <span>🤖 <strong style={{ color: '#58a6ff' }}>{analysisResult.model_used}</strong></span>
                {analysisResult.metrics && (
                    <>
                        <span>📝 <strong style={{ color: '#c9d1d9' }}>{analysisResult.metrics.code_lines}</strong> lines analyzed</span>
                        <span>📊 <strong style={{ color: '#c9d1d9' }}>{analysisResult.metrics.log_size_kb}</strong> KB logs</span>
                        {analysisResult.metrics.glue_script_kb || analysisResult.metrics.operator_script_kb ? (
                            <span>⚙️ <strong style={{ color: '#ffa657' }}>{analysisResult.metrics.operator_script_kb || analysisResult.metrics.glue_script_kb}</strong> KB {analysisResult.operator_type || 'Glue'} script
                                {(analysisResult.metrics.operator_script_truncated || analysisResult.metrics.glue_script_truncated) && <span style={{ color: '#8b949e' }}> (truncated)</span>}
                            </span>
                        ) : null}
                    </>
                )}
                {analysisResult.glue_job_name || analysisResult.operator_name ? (
                    <span>🔧 <strong style={{ color: '#79c0ff' }}>{analysisResult.operator_name || analysisResult.glue_job_name}</strong></span>
                ) : null}
            </div>
            <button
                onClick={() => setShowPrompt(!showPrompt)}
                style={{
                    padding: '6px 12px',
                    fontSize: '13px',
                    backgroundColor: '#238636',
                    color: '#fff',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontWeight: '500'
                }}
            >
                {showPrompt ? '👁️ Hide Prompt' : '👁️ Show Prompt'}
            </button>
        </div>
    </div>
);

const PromptDisplay = ({ prompt }) => (
    <div style={{
        marginBottom: '15px',
        padding: '15px',
        backgroundColor: '#0d1117',
        border: '1px solid #30363d',
        borderRadius: '6px'
    }}>
        <h3 style={{ margin: '0 0 10px 0', fontSize: '16px', color: '#8b949e' }}>Prompt Used:</h3>
        <pre style={{
            margin: 0,
            fontSize: '12px',
            whiteSpace: 'pre-wrap',
            wordWrap: 'break-word',
            color: '#c9d1d9'
        }}>{prompt}</pre>
    </div>
);

const RootCauseBox = ({ parsed }) => (
    <div style={{
        padding: '15px',
        backgroundColor: '#1a1f2e',
        border: '2px solid #d32f2f',
        borderRadius: '8px'
    }}>
        <h3 style={{
            margin: '0 0 10px 0',
            fontSize: '16px',
            color: '#ff6b6b',
            fontWeight: '600'
        }}>🔍 Root Cause</h3>
        <SafeMarkdown text={parsed.root_cause} style={{ margin: 0, color: '#c9d1d9', lineHeight: '1.6' }} />
    </div>
);

const ResolutionBox = ({ parsed }) => (
    <div style={{
        padding: '15px',
        backgroundColor: '#1a2e1a',
        border: '2px solid #28a745',
        borderRadius: '8px'
    }}>
        <h3 style={{
            margin: '0 0 10px 0',
            fontSize: '16px',
            color: '#6bff6b',
            fontWeight: '600'
        }}>✅ Resolution</h3>
        <SafeMarkdown text={parsed.resolution} style={{ margin: 0, color: '#c9d1d9', lineHeight: '1.6' }} />
    </div>
);

const AdditionalDetails = ({ parsed }) => {
    if (!parsed.additional_details) return null;
    
    return (
        <div style={{
            padding: '15px',
            backgroundColor: '#161b22',
            border: '1px solid #30363d',
            borderRadius: '8px'
        }}>
            <h3 style={{
                margin: '0 0 10px 0',
                fontSize: '16px',
                color: '#58a6ff',
                fontWeight: '600'
            }}>📋 Additional Details</h3>
            <SafeMarkdown text={parsed.additional_details} style={{ color: '#c9d1d9', lineHeight: '1.6' }} />
        </div>
    );
};

const StructuredAnalysis = ({ analysisResult, showPrompt, setShowPrompt }) => (
    <div style={{ marginTop: '20px' }}>
        <AnalysisMetrics
            analysisResult={analysisResult}
            showPrompt={showPrompt}
            setShowPrompt={setShowPrompt}
        />
        {showPrompt && <PromptDisplay prompt={analysisResult.prompt} />}
        <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '15px',
            marginBottom: '15px'
        }}>
            <RootCauseBox parsed={analysisResult.parsed} />
            <ResolutionBox parsed={analysisResult.parsed} />
        </div>
        {analysisResult.parsed.additional_details && (
            <AdditionalDetails parsed={analysisResult.parsed} />
        )}
    </div>
);

const RawAnalysis = ({ displayTitle, displayContent, analysisResult, showPrompt, setShowPrompt }) => (
    <div style={{
        marginTop: '20px',
        padding: '15px',
        backgroundColor: '#161b22',
        border: '1px solid #30363d',
        borderRadius: '6px'
    }}>
        <h2 style={{ margin: '0 0 10px 0', fontSize: '18px', color: '#58a6ff' }}>{displayTitle}</h2>
        {analysisResult && (
            <div style={{
                marginBottom: '10px',
                display: 'flex',
                alignItems: 'center',
                gap: '15px'
            }}>
                <span style={{
                    backgroundColor: '#1f6feb',
                    color: '#fff',
                    padding: '6px 12px',
                    borderRadius: '6px',
                    fontSize: '14px',
                    fontWeight: '600',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '6px'
                }}>
                    <span>🤖</span>
                    <span>{analysisResult.model_used}</span>
                </span>
                <button
                    onClick={() => setShowPrompt(!showPrompt)}
                    style={{
                        padding: '6px 12px',
                        fontSize: '13px',
                        backgroundColor: '#238636',
                        color: '#fff',
                        border: 'none',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontWeight: '500'
                    }}
                >
                    {showPrompt ? '👁️ Hide Prompt' : '👁️ Show Prompt'}
                </button>
            </div>
        )}
        {showPrompt && analysisResult && <PromptDisplay prompt={analysisResult.prompt} />}
        <pre style={{
            margin: 0,
            maxHeight: '500px',
            overflow: 'auto',
            whiteSpace: 'pre-wrap',
            wordWrap: 'break-word'
        }}>{displayContent}</pre>
    </div>
);
