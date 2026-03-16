// Configuration for Task Analyzer Plugin
const CONFIG = {
    // API Configuration
    API: {
        BASE_URL: '/api/v2',
        ENDPOINTS: {
            TASK_INSTANCE: '/dags/{dagId}/dagRuns/{runId}/taskInstances/{taskId}',
            LOGS: '/dags/{dagId}/dagRuns/{runId}/taskInstances/{taskId}/logs/{tryNumber}',
            DAG_SOURCE: '/dagSources/{dagId}'
        }
    },
    
    // Default values
    DEFAULTS: {
        TRY_NUMBER: 1
    },
    
    // UI Messages
    MESSAGES: {
        NO_TASK_INFO: 'Task information not available',
        NO_LOGS: 'No logs available for this task',
        CONTEXT_NOT_LOADED: 'Context not loaded yet',
        NO_DAG_ID: 'DAG ID not available'
    }
};
