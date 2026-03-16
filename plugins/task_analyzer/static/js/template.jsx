/** @jsx React.createElement */
function TaskAnalyzerTemplate({ 
    taskInfo, 
    models, 
    selectedModel, 
    setSelectedModel,
    analyzeFail,
    showDagContext,
    showDagCode,
    showLogs,
    testAWS,
    analysisResult,
    showPrompt,
    setShowPrompt,
    displayContent,
    displayTitle
}) {
    const [showGlueScript, setShowGlueScript] = React.useState(false);
    
    const handleShowGlueScript = () => {
        if (analysisResult && analysisResult.prompt) {
            // Extract operator script from prompt
            const scriptMatch = analysisResult.prompt.match(/## .*? Script[\s\S]*?```\n([\s\S]*?)```/);
            if (scriptMatch) {
                setShowGlueScript(!showGlueScript);
            } else {
                alert('No operator script found in analysis');
            }
        }
    };
    
    const hasOperatorScript = analysisResult && (analysisResult.operator_type || analysisResult.glue_job_name);
    
    // Map operator types to button labels
    const getOperatorButtonLabel = () => {
        if (!analysisResult) return 'Script';
        const opType = analysisResult.operator_type;
        if (!opType) return 'Glue Script';
        
        // If it's already a label (contains space), use it
        if (opType.includes(' ')) return opType;
        
        // Otherwise map short names to labels
        const labelMap = {
            'python': 'Python Code',
            'bash': 'Bash Script',
            'glue': 'AWS Glue Job',
            'athena': 'Athena Query',
            'redshift': 'Redshift Query',
            'emr': 'EMR Script',
            'emr_serverless': 'EMR Serverless Script',
            'dbt': 'DBT Models'
        };
        return labelMap[opType] || opType;
    };
    
    const operatorLabel = getOperatorButtonLabel();
    
    return (
        <div style={{ minHeight: '100vh'}}>
            <h1>Task Failure Analyzer</h1>
            <div className="task-info">
                <p><strong>DAG ID:</strong> {taskInfo.dagId}</p>
                <p><strong>Task ID:</strong> {taskInfo.taskId}</p>
                <p><strong>Run ID:</strong> {taskInfo.runId}</p>
                <p><strong>State:</strong> <span style={{
                    backgroundColor: taskInfo.state === 'Failed' ? '#d32f2f' : taskInfo.state === 'Success' ? '#28a745' : '#ffc107',
                    color: taskInfo.state === 'Failed' || taskInfo.state === 'Success' ? '#fff' : '#000',
                    padding: '4px 8px',
                    borderRadius: '4px',
                    fontWeight: '500'
                }}>{taskInfo.state}</span></p>
                <p><strong>Error:</strong> {taskInfo.error}</p>
            </div>
            <div style={{marginBottom: '15px', display: 'flex', alignItems: 'center', gap: '10px'}}>
                <label style={{fontWeight: '600', color: '#c9d1d9'}}>🤖 Select Model:</label>
                <select value={selectedModel} onChange={(e) => setSelectedModel(e.target.value)} style={{padding: '8px 12px', borderRadius: '6px', border: '1px solid #30363d', backgroundColor: '#0d1117', color: '#c9d1d9', fontSize: '14px', fontWeight: '500', cursor: 'pointer'}}>
                    {models.map(m => <option key={m.key} value={m.key}>{m.name}</option>)}
                </select>
            </div>
            <button onClick={analyzeFail} className="btn btn-primary">
                Analyze with LLM
            </button>
            <button onClick={showDagContext} style={{backgroundColor: '#9c27b0', color: '#fff', border: 'none', padding: '10px 20px', borderRadius: '4px', cursor: 'pointer', fontWeight: '500', marginRight: '10px'}}>
                Task Context
            </button>
            <button onClick={showDagCode} className="btn btn-success">
                DAG Code
            </button>
            <button onClick={showLogs} className="btn btn-warning">
                Logs
            </button>
            {hasOperatorScript && (
                <button onClick={handleShowGlueScript} style={{backgroundColor: '#ff9800', color: '#fff', border: 'none', padding: '10px 20px', borderRadius: '4px', cursor: 'pointer', fontWeight: '500', marginRight: '10px'}}>
                    {showGlueScript ? `Hide ${operatorLabel}` : `Show ${operatorLabel}`}
                </button>
            )}
            <button onClick={testAWS} style={{backgroundColor: '#17a2b8', color: '#fff', border: 'none', padding: '10px 20px', borderRadius: '4px', cursor: 'pointer', fontWeight: '500', marginRight: '10px'}}>
                Test AWS
            </button>
            {showGlueScript && hasOperatorScript && (
                <div style={{
                    marginTop: '15px',
                    padding: '15px',
                    backgroundColor: '#0d1117',
                    border: '1px solid #30363d',
                    borderRadius: '6px'
                }}>
                    <h3 style={{ margin: '0 0 10px 0', fontSize: '16px', color: '#ffa657' }}>
                        ⚙️ {operatorLabel}: {analysisResult.operator_name || analysisResult.glue_job_name || 'Script'}
                    </h3>
                    {analysisResult.metrics && (analysisResult.metrics.operator_script_truncated || analysisResult.metrics.glue_script_truncated) && (
                        <div style={{
                            padding: '8px',
                            backgroundColor: '#1a1f2e',
                            border: '1px solid #ffa657',
                            borderRadius: '4px',
                            marginBottom: '10px',
                            color: '#ffa657',
                            fontSize: '13px'
                        }}>
                            ⚠️ Script was truncated to fit token limits. Only relevant sections are shown.
                        </div>
                    )}
                    <pre style={{
                        margin: 0,
                        fontSize: '12px',
                        whiteSpace: 'pre-wrap',
                        wordWrap: 'break-word',
                        color: '#c9d1d9',
                        maxHeight: '500px',
                        overflow: 'auto'
                    }}>{analysisResult.prompt.match(/## .*? Script[\s\S]*?```\n([\s\S]*?)```/)?.[1] || 'Script not available'}</pre>
                </div>
            )}
            {analysisResult && analysisResult.parsed ? (
                <StructuredAnalysis 
                    analysisResult={analysisResult}
                    showPrompt={showPrompt}
                    setShowPrompt={setShowPrompt}
                />
            ) : displayContent && (
                <RawAnalysis 
                    displayTitle={displayTitle}
                    displayContent={displayContent}
                    analysisResult={analysisResult}
                    showPrompt={showPrompt}
                    setShowPrompt={setShowPrompt}
                />
            )}
        </div>
    );
}
