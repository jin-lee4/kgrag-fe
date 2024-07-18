-- Create the uploaded_pdfs table
CREATE TABLE uploaded_pdfs (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  filename VARCHAR(255) NOT NULL,
  file_handle VARCHAR(255) NOT NULL,
  upload_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
