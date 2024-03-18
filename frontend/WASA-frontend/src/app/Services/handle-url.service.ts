export class HandleUrlService {
    data : any = [];

  validateUrl(value : string) {
    return /^(?:(?:(?:https?|ftp):)?\/\/)(?:\S+(?::\S*)?@)?(?:(?!(?:10|127)(?:\.\d{1,3}){3})(?!(?:169\.254|192\.168)(?:\.\d{1,3}){2})(?!172\.(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2})(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}(?:\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))|(?:(?:[a-z\u00a1-\uffff0-9]-*)*[a-z\u00a1-\uffff0-9]+)(?:\.(?:[a-z\u00a1-\uffff0-9]-*)*[a-z\u00a1-\uffff0-9]+)*(?:\.(?:[a-z\u00a1-\uffff]{2,})))(?::\d{2,5})?(?:[/?#]\S*)?$/i.test(value);
  }

  OnSubmitUrl(url : string){
    let validUrlFlag = true;
    let errorMessage = "Something doesn't look right with the url your submitted. The url: "+ url +" has the following issues:\n"

    // url must be long enough to be an http request
    if (!(url.length > 7)) {
      errorMessage += "\nIt is too short. URLs should be at least 8 characters long."
      validUrlFlag = false;
    }

    // url must pass form logic for what a url looks like
    if (!this.validateUrl(url)) {
      // handle case where the user forgot https://
      url = "https://"+url
      if (!this.validateUrl(url)) {
        errorMessage += "\nThe url is not formatted correctly."
        validUrlFlag = false;
      }
    }

    if (validUrlFlag) {
      return url
    }
    
    errorMessage += "\n\nPlease try again with a new URL."
    alert(errorMessage)
    return '';
  }
}