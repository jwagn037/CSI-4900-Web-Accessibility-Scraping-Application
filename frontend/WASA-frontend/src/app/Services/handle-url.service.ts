export class HandleUrlService {
    data : any = [];

  OnSubmitUrl(url : string){
    let control: HTMLInputElement = document.createElement("input");
    control.type = "url";
    control.value = url;

    // url must be long enough to be an http request
    if (!(control.value.length > 7)) {
      alert(control.value + " is too short.")
      return '';
    }

    // url must pass form logic for what a url looks like
    if (!control.checkValidity()) { 
      alert(control.value + " is not a URL.")
      return '';
    } 
    
    return url;
  }
}