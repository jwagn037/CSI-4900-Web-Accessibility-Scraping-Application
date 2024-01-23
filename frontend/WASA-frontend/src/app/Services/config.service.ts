import { Injectable, inject } from "@angular/core";
import { HttpClient, HttpHeaders } from '@angular/common/http';

@Injectable({
    providedIn: 'root'
})
export class ConfigService {
  http : HttpClient = inject(HttpClient)
  apiUrl: string = 'http://127.0.0.1:5000/url';

  getArticle(articleUrl: string) {
    // construct the basic get request the API expects
    const fullUrl = `${this.apiUrl}?data=${articleUrl}`;

    this.http.get<{name: string}>(fullUrl)
      .subscribe(data => {
        console.log(data);
      });
  }
}