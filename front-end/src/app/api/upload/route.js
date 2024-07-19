import { extname } from 'path';
import { NextRequest, NextResponse } from 'next/server';
import { Storage } from '@google-cloud/storage';
import * as dateFn from 'date-fns';

function sanitizeFilename(filename) {
  return filename.replace(/[^a-zA-Z0-9_\u0600-\u06FF.]/g, '_');
}

export async function POST(request) {
  const formData = await request.formData();

  const file = formData.get('file');
  if (!file) {
    return NextResponse.json(
      { error: 'File blob is required.' },
      { status: 400 }
    );
  }

  const buffer = Buffer.from(await file.arrayBuffer());

  const relativeUploadDir = `${dateFn.format(Date.now(), 'dd-MM-Y')}`;
  const uniqueSuffix = `${Date.now()}_${Math.round(Math.random() * 1e9)}`;
  const fileExtension = extname(file.name);
  const originalFilename = file.name.replace(/\.[^/.]+$/, '');
  const sanitizedFilename = sanitizeFilename(originalFilename);
  const filename = `${sanitizedFilename}_${uniqueSuffix}${fileExtension}`;

  console.log('filename : ' + filename);

  const storage = new Storage({ keyFilename: process.env.GOOGLE_APPLICATION_CREDENTIALS });
  const bucketName = process.env.GOOGLE_CLOUD_BUCKET;
  const destination = `${relativeUploadDir}/${filename}`;

  try {
    const bucket = storage.bucket(bucketName);
    const fileInBucket = bucket.file(destination);

    await fileInBucket.save(buffer);

    console.log('Uploaded file path:', destination);
    return NextResponse.json({ done: 'ok', filename: filename, filePath: destination }, { status: 200 });

  } catch (e) {
    console.error('Error while trying to upload a file\n', e);
    return NextResponse.json(
      { error: 'Something went wrong.' },
      { status: 500 }
    );
  }
}
