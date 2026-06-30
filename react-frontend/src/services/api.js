// API Service wrapper

export const api = {
  // Health
  checkHealth: async () => {
    const res = await fetch('/api/health');
    return res.json();
  },
  getMetrics: async () => {
    const res = await fetch('/api/health/metrics');
    return res.json();
  },
  getModels: async () => {
    const res = await fetch('/api/health/models');
    return res.json();
  },
  
  // Vault
  getRecords: async () => {
    const res = await fetch('/api/vault/records');
    return res.json();
  },
  getRecord: async (id) => {
    const res = await fetch(`/api/vault/records/${id}`);
    return res.json();
  },
  uploadPrescription: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch('/api/vault/upload-prescription', {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) throw new Error('Upload failed');
    return res.json();
  },

  // Care Router
  anonymizeData: async (data) => {
    const res = await fetch('/api/care/anonymize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ patient_data: data }),
    });
    return res.json();
  },
  routePatient: async (clinicalIntent, city) => {
    const res = await fetch('/api/care/route', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ clinical_intent: clinicalIntent, city }),
    });
    return res.json();
  },
  checkDrugs: async (medications) => {
    const res = await fetch('/api/care/drug-check', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ medications }),
    });
    return res.json();
  }
};
