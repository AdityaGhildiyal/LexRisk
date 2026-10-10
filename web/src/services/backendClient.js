const axios = require('axios');
const FormData = require('form-data');

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

exports.processContract = async (file) => {
  const formData = new FormData();
  formData.append('file', file.buffer, {
    filename: file.originalname,
    contentType: file.mimetype,
  });

  const response = await axios.post(`${BACKEND_URL}/pipeline/process`, formData, {
    headers: formData.getHeaders(),
    timeout: 300000, // 5 minutes
    maxContentLength: Infinity,
    maxBodyLength: Infinity,
  });

  return response.data;
};
