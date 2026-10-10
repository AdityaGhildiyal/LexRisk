const backendClient = require('../services/backendClient');
const { v4: uuidv4 } = require('uuid');

exports.showUploadForm = (req, res) => {
  res.render('upload', { error: null });
};

exports.handleUpload = async (req, res) => {
  if (!req.file) {
    return res.render('upload', { error: 'Please select a PDF or DOCX file to upload.' });
  }

  try {
    const report = await backendClient.processContract(req.file);
    const reportId = uuidv4();
    
    // Store report in session (demo scope — no DB needed)
    if (!req.session.reports) req.session.reports = {};
    req.session.reports[reportId] = report;
    
    return res.redirect(`/report/${reportId}`);
  } catch (err) {
    console.error('Pipeline error:', err.message);
    const userMessage = err.response?.data?.detail || err.message || 'Failed to process contract. Please try again.';
    return res.render('upload', { error: userMessage });
  }
};
