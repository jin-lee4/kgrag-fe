import { NextResponse } from 'next/server';
import { Storage } from '@google-cloud/storage';
import vision from '@google-cloud/vision';
import { readFileSync } from 'fs';
import { tmpdir } from 'os';
import { join } from 'path';

export async function POST(request) {
  try {
    const { filePath } = await request.json();
    console.log('File path:', filePath);
    console.log('Bucket name:', process.env.GOOGLE_CLOUD_BUCKET);
    console.log('Service Account Key:', process.env.GOOGLE_APPLICATION_CREDENTIALS);

    const client = new vision.ImageAnnotatorClient({ keyFilename: process.env.GOOGLE_APPLICATION_CREDENTIALS });
    const storage = new Storage({ keyFilename: process.env.GOOGLE_APPLICATION_CREDENTIALS });

    const outputDirectory = `gs://${process.env.GOOGLE_CLOUD_BUCKET}/output/`;
    console.log('Output directory:', outputDirectory);

    const requestPayload = {
      requests: [
        {
          inputConfig: {
            mimeType: 'application/pdf',
            gcsSource: {
              uri: `gs://${process.env.GOOGLE_CLOUD_BUCKET}/${filePath}`,
            },
          },
          features: [{ type: 'DOCUMENT_TEXT_DETECTION' }],
          outputConfig: {
            gcsDestination: {
              uri: outputDirectory,
            },
          },
        },
      ],
    };

    const [operation] = await client.asyncBatchAnnotateFiles(requestPayload);
    const [filesResponse] = await operation.promise();

    console.log('Operation completed. Checking for output files.');

    const [files] = await storage.bucket(process.env.GOOGLE_CLOUD_BUCKET).getFiles({ prefix: 'output/' });
    if (files.length === 0) {
      throw new Error('No output files found.');
    }

    const outputFile = files[0]; // Assuming there's at least one output file
    const destinationFilePath = join(tmpdir(), outputFile.name.split('/').pop());

    await outputFile.download({ destination: destinationFilePath });

    const outputFileContent = readFileSync(destinationFilePath, 'utf8');
    const jsonContent = JSON.parse(outputFileContent);

    const textAnnotations = jsonContent.responses[0].fullTextAnnotation.text;

    console.log('Extracted text:', textAnnotations);

    return NextResponse.json({ text: textAnnotations });
  } catch (error) {
    console.error('Error during OCR processing:', error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
