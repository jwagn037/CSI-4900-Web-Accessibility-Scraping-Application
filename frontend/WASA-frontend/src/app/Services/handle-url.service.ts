import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from "@angular/core";
import { ConfigService } from './config.service';


export class HandleUrlService {
    data : any = [];

    OnSubmitUrl(url : string){
        let targetUrl : string = ''
        // URL Validation
        let control: HTMLInputElement = document.createElement("input");
        control.type = "url";
        control.value = url;
        // URLs must pass form validity checker, and have 9+ characters 
        let isValid: boolean = (control.checkValidity() && control.value.length > 8);
    
        if (!isValid) {
          alert(control.value + " is not a valid URL.")
          return '';
        } else {
          // don't pass the user's input directly
           targetUrl = control.value;
        }
        
        return url;

      }
}