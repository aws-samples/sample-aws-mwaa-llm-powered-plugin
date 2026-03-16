/** @jsx React.createElement */
// Utility functions for Task Analyzer

const getSeverityColor = (severity) => {
    if (severity === 'Critical') return '#ff6b6b';
    if (severity === 'High') return '#ffa657';
    return '#ffd93d';
};

const renderMarkdown = (text) => {
    if (!text) return '';
    // Use marked library to convert markdown to HTML
    return marked.parse(text, { breaks: true, gfm: true });
};
