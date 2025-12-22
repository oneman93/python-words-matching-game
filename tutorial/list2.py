import google.cloud.storage as gcs

client = gcs.Client()

blobs = client.list_blobs("mybucket")
blob = next(blobs)  # TypeError: 'HTTPIterator' object is not an iterator

blob = blobs.__next__()  # AttributeError: 'HTTPIterator' object has no attribute '__next__'
