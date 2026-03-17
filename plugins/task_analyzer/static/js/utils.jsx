/** @jsx React.createElement */
// Utility functions for Task Analyzer

const getSeverityColor = (severity) => {
    if (severity === 'Critical') return '#ff6b6b';
    if (severity === 'High') return '#ffa657';
    return '#ffd93d';
};

const renderMarkdown = (text) => {
    if (!text) return '';
    const rawHtml = marked.parse(text, { breaks: true, gfm: true });
    return DOMPurify.sanitize(rawHtml);
};
