const { useState, useEffect, useRef } = React;

function TaskAnalyzer() {
    const [taskInfo, setTaskInfo] = useState({
        dagId: '',
        taskId: '',
        runId: '',
        state: '',
        error: ''
    });
    const [fullContext, setFullContext] = useState(null);
    const [displayContent, setDisplayContent] = useState(null);
    const [displayTitle, setDisplayTitle] = useState('');
    const [models, setModels] = useState([]);
    const [selectedModel, setSelectedModel] = useState('');
    const [analysisResult, setAnalysisResult] = useState(null);
    const [showPrompt, setShowPrompt] = useState(false);
    const analysisCache = useRef({});
    const currentTaskKey = useRef('')
    

    useEffect(() => {
        fetch('/task-analyzer/api/models')
            .then(res => res.json())
            .then(data => {
                setModels(data.models);
                setSelectedModel(data.default);
            })
            .catch(err => console.error('Error loading models:', err));
    }, []);
    
    useEffect(() => {
        const fetchTaskData = () => {
            let parentUrl = '';
            try {
                parentUrl = window.parent.location.pathname;
            } catch (e) {
                parentUrl = window.location.pathname;
            }
            
            const pathParts = parentUrl.split('/').filter(p => p);
            const dagIndex = pathParts.indexOf('dags');
            const taskIndex = pathParts.indexOf('tasks');
            const runIndex = pathParts.indexOf('runs');
            const mappedIndex = pathParts.indexOf('mapped');
            
            const dagId = dagIndex >= 0 ? decodeURIComponent(pathParts[dagIndex + 1]) : 'N/A';
            const taskId = taskIndex >= 0 ? decodeURIComponent(pathParts[taskIndex + 1]) : 'N/A';
            const runId = runIndex >= 0 ? decodeURIComponent(pathParts[runIndex + 1]) : 'N/A';
            const mapIndexValue = mappedIndex >= 0 ? decodeURIComponent(pathParts[mappedIndex + 1]) : null;
            
            console.log('Task Analyzer Debug:', { parentUrl, dagId, taskId, runId, mapIndexValue, mappedIndex });
            
            if (dagId !== 'N/A' && taskId !== 'N/A' && runId !== 'N/A') {
                // Build URL with map_index in path for mapped tasks (only if >= 0)
                let taskIdWithIndex = taskId;
                if (mapIndexValue !== null && parseInt(mapIndexValue) >= 0) {
                    taskIdWithIndex = `${taskId}/${mapIndexValue}`;
                }
                
                let url = CONFIG.API.BASE_URL + CONFIG.API.ENDPOINTS.TASK_INSTANCE
                    .replace('{dagId}', encodeURIComponent(dagId))
                    .replace('{runId}', encodeURIComponent(runId))
                    .replace('{taskId}', taskIdWithIndex);
                
                console.log('Fetching task instance from:', url);
                
                fetch(url, {
                    cache: 'no-store',
                    headers: {
                        'Cache-Control': 'no-cache',
                        'Pragma': 'no-cache'
                    }
                })
                    .then(res => res.json())
                    .then(data => {
                        console.log('Task instance response:', data);
                        setFullContext(data);
                        let errorMsg = 'No error details';
                        if (data.state === 'failed') {
                            const bashCmd = data.rendered_fields?.bash_command;
                            if (bashCmd) {
                                errorMsg = `Command failed: ${bashCmd} - Check logs for details`;
                            } else {
                                errorMsg = `${data.operator || 'Task'} failed - Check logs for details`;
                            }
                        } else if (data.note) {
                            errorMsg = data.note;
                        }
                        const state = data.state || 'unknown';
                        const capitalizedState = state.charAt(0).toUpperCase() + state.slice(1);
                        const newTaskInfo = {
                            dagId: data.dag_id || dagId,
                            taskId: data.task_id || taskId,
                            runId: data.dag_run_id || runId,
                            mapIndex: data.map_index !== undefined ? data.map_index : mapIndexValue,
                            state: capitalizedState,
                            error: errorMsg,
                            timestamp: Date.now()
                        };
                        
                        const taskKey = `${newTaskInfo.dagId}_${newTaskInfo.taskId}_${newTaskInfo.runId}`;
                        if (taskKey !== currentTaskKey.current) {
                            currentTaskKey.current = taskKey;
                            
                            if (analysisCache.current[taskKey]) {
                                const cached = analysisCache.current[taskKey];
                                setAnalysisResult(cached.analysisResult);
                                setDisplayContent(cached.displayContent);
                                setDisplayTitle(cached.displayTitle);
                            } else {
                                setAnalysisResult(null);
                                setDisplayContent(null);
                                setDisplayTitle('');
                            }
                        }
                        
                        setTaskInfo(newTaskInfo);
                    })
                    .catch(err => {
                        console.error('API Error:', err);
                        setTaskInfo({
                            dagId: dagId,
                            taskId: taskId,
                            runId: runId,
                            state: 'API Error',
                            error: err.message
                        });
                    });
            } else {
                setTaskInfo({
                    dagId: dagId,
                    taskId: taskId,
                    runId: runId,
                    state: 'N/A',
                    error: 'N/A'
                });
            }
        };
        
        fetchTaskData();
        
        const intervalId = setInterval(() => {
            try {
                const currentUrl = window.parent.location.href;
                if (currentUrl !== window.lastCheckedUrl) {
                    window.lastCheckedUrl = currentUrl;
                    fetchTaskData();
                }
            } catch (e) {
                // Cross-origin access blocked
            }
        }, 500);
        
        return () => clearInterval(intervalId);
    }, []);
    
    const showDagContext = () => {
        setAnalysisResult(null);
        const content = fullContext 
            ? JSON.stringify(fullContext, null, 2)
            : CONFIG.MESSAGES.CONTEXT_NOT_LOADED;
        setDisplayTitle('Task Context');
        setDisplayContent(content);
    };
    
    const analyzeFail = () => {
        const taskKey = `${taskInfo.dagId}_${taskInfo.taskId}_${taskInfo.runId}_${selectedModel}`;
        
        // Always clear and re-analyze (no caching by model)
        setDisplayTitle('Analyze with LLM');
        setDisplayContent('Analyzing task failure...');
        setAnalysisResult(null);
        setShowPrompt(false);
        
        const dagContext = fullContext ? JSON.stringify(fullContext, null, 2) : null;
        let logs = null;
        let dagCode = null;
        
        const tryNumber = fullContext?.try_number || CONFIG.DEFAULTS.TRY_NUMBER;
        
        // Build logs URL with query parameter for mapped tasks
        let logsUrl = CONFIG.API.BASE_URL + CONFIG.API.ENDPOINTS.LOGS
            .replace('{dagId}', encodeURIComponent(taskInfo.dagId))
            .replace('{runId}', encodeURIComponent(taskInfo.runId))
            .replace('{taskId}', encodeURIComponent(taskInfo.taskId))
            .replace('{tryNumber}', tryNumber);
        
        if (taskInfo.mapIndex !== undefined && taskInfo.mapIndex !== null && taskInfo.mapIndex >= 0) {
            logsUrl += `?map_index=${taskInfo.mapIndex}`;
        }
        
        const dagUrl = CONFIG.API.BASE_URL + CONFIG.API.ENDPOINTS.DAG_SOURCE.replace('{dagId}', taskInfo.dagId);
        
        Promise.all([
            fetch(logsUrl).then(r => r.json()).then(d => logs = d.content).catch(() => logs = 'Not available'),
            fetch(dagUrl).then(r => r.json()).then(d => dagCode = d.content).catch(() => dagCode = 'Not available')
        ]).finally(() => {
            fetch('/task-analyzer/api/analyze-task', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    dag_id: taskInfo.dagId,
                    task_id: taskInfo.taskId,
                    run_id: taskInfo.runId,
                    state: taskInfo.state,
                    error: taskInfo.error,
                    context: dagContext,
                    dag_code: dagCode,
                    logs: logs,
                    model: selectedModel
                })
            })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        // Parse the markdown-style response into sections
                        const analysis = data.analysis;
                        
                        console.log('Raw analysis:', analysis.substring(0, 200));
                        
                        // Extract sections - be flexible with formatting
                        // Try different patterns for section headers
                        const rootCauseMatch = analysis.match(/###?\s*🔍\s*ROOT CAUSE\s*[\r\n]+([\s\S]*?)(?=###?\s*✅\s*RESOLUTION|$)/i);
                        const resolutionMatch = analysis.match(/###?\s*✅\s*RESOLUTION\s*[\r\n]+([\s\S]*?)(?=###?\s*📋\s*ADDITIONAL DETAILS|$)/i);
                        const additionalMatch = analysis.match(/###?\s*📋\s*ADDITIONAL DETAILS\s*[\r\n]+([\s\S]*?)$/i);
                        
                        console.log('Parsing results:', {
                            rootCause: rootCauseMatch ? 'Found' : 'Not found',
                            resolution: resolutionMatch ? 'Found' : 'Not found', 
                            additional: additionalMatch ? 'Found' : 'Not found'
                        });
                        
                        // If sections not found, try to split by headers anyway
                        let rootCause = rootCauseMatch ? rootCauseMatch[1].trim() : '';
                        let resolution = resolutionMatch ? resolutionMatch[1].trim() : '';
                        let additional = additionalMatch ? additionalMatch[1].trim() : '';
                        
                        // Fallback: if no sections found, put everything in root cause
                        if (!rootCause && !resolution && !additional) {
                            rootCause = analysis;
                        }
                        
                        const parsed = {
                            root_cause: rootCause,
                            resolution: resolution,
                            additional_details: additional
                        };
                        
                        const result = {...data, parsed};
                        setAnalysisResult(result);
                        
                        analysisCache.current[taskKey] = {
                            analysisResult: result,
                            displayContent: data.analysis,
                            displayTitle: 'Analyze with LLM'
                        };
                        
                        setDisplayContent(data.analysis);
                    } else {
                        setDisplayContent(`Error: ${data.error}`);
                    }
                })
                .catch(err => setDisplayContent(`Error: ${err.message}`));
        });
    };
    
    const testAWS = () => {
        setAnalysisResult(null);
        setDisplayTitle('Test AWS');
        setDisplayContent('Loading...');
        
        fetch('/task-analyzer/api/test-aws')
            .then(res => {
                if (!res.ok) {
                    throw new Error(`HTTP ${res.status}: ${res.statusText}`);
                }
                return res.json();
            })
            .then(data => {
                if (data.success) {
                    const output = `Bucket: ${data.bucket}\nObject Count: ${data.count}\n\nObjects:\n${JSON.stringify(data.objects, null, 2)}`;
                    setDisplayContent(output);
                } else {
                    setDisplayContent(`Error: ${data.error}\nType: ${data.error_type}`);
                }
            })
            .catch(err => {
                setDisplayContent('Error testing AWS: ' + err.message);
            });
    };
    
    const showLogs = () => {
        setAnalysisResult(null);
        if (taskInfo.dagId === 'N/A' || taskInfo.taskId === 'N/A' || taskInfo.runId === 'N/A') {
            setDisplayTitle('Logs');
            setDisplayContent(CONFIG.MESSAGES.NO_TASK_INFO);
            return;
        }
        
        const tryNumber = fullContext?.try_number || CONFIG.DEFAULTS.TRY_NUMBER;
        
        // Build URL with query parameter for mapped tasks
        let url = CONFIG.API.BASE_URL + CONFIG.API.ENDPOINTS.LOGS
            .replace('{dagId}', encodeURIComponent(taskInfo.dagId))
            .replace('{runId}', encodeURIComponent(taskInfo.runId))
            .replace('{taskId}', encodeURIComponent(taskInfo.taskId))
            .replace('{tryNumber}', tryNumber);
        
        if (taskInfo.mapIndex !== undefined && taskInfo.mapIndex !== null && taskInfo.mapIndex >= 0) {
            url += `?map_index=${taskInfo.mapIndex}`;
        }
        
        setDisplayTitle('Logs');
        setDisplayContent('Loading...');
        
        fetch(url)
            .then(res => {
                if (!res.ok) {
                    throw new Error(`HTTP ${res.status}: ${res.statusText}`);
                }
                return res.json();
            })
            .then(data => {
                let logs = data.content;
                if (typeof logs !== 'string') {
                    logs = JSON.stringify(data, null, 2);
                }
                setDisplayContent(logs || CONFIG.MESSAGES.NO_LOGS);
            })
            .catch(err => {
                setDisplayContent('Error fetching logs: ' + err.message);
            });
    };
    
    const showDagCode = () => {
        setAnalysisResult(null);
        if (taskInfo.dagId === 'N/A') {
            setDisplayTitle('DAG Code');
            setDisplayContent(CONFIG.MESSAGES.NO_DAG_ID);
            return;
        }
        
        const url = CONFIG.API.BASE_URL + CONFIG.API.ENDPOINTS.DAG_SOURCE.replace('{dagId}', taskInfo.dagId);
        
        setDisplayTitle('DAG Code');
        setDisplayContent('Loading...');
        
        fetch(url)
            .then(res => {
                if (!res.ok) {
                    throw new Error(`HTTP ${res.status}: ${res.statusText}`);
                }
                return res.json();
            })
            .then(data => {
                const code = data.content || JSON.stringify(data, null, 2);
                setDisplayContent(code);
            })
            .catch(err => {
                setDisplayContent('Error fetching DAG code: ' + err.message);
            });
    };
    
    return (
        <TaskAnalyzerTemplate
            taskInfo={taskInfo}
            models={models}
            selectedModel={selectedModel}
            setSelectedModel={setSelectedModel}
            analyzeFail={analyzeFail}
            showDagContext={showDagContext}
            showDagCode={showDagCode}
            showLogs={showLogs}
            testAWS={testAWS}
            analysisResult={analysisResult}
            showPrompt={showPrompt}
            setShowPrompt={setShowPrompt}
            displayContent={displayContent}
            displayTitle={displayTitle}
        />
    );
}

ReactDOM.render(<TaskAnalyzer />, document.getElementById('root'));
