function(doc, req) {
  if(doc.type == 'example' || doc.deleted) {
      return true;
  } else {
      return false;
  }  
}
