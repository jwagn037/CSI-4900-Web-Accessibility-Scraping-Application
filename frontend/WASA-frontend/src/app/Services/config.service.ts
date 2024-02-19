import { Injectable, inject } from "@angular/core";
import { HttpClient } from '@angular/common/http';
import { Observable, Subject } from "rxjs";

@Injectable({
    providedIn: 'root'
})
export class ConfigService {
  http : HttpClient = inject(HttpClient)
  apiUrl: string = 'http://127.0.0.1:5000/url';
  private json = new Subject<any>();

  // Updates target URL in shared service ConfigService.
  // Used by UrlSubmissionForm.
  // Awesome Stackoverflow thread on this pattern: https://stackoverflow.com/questions/63888794/how-to-refresh-a-component-from-another-in-angular
  getArticle(articleUrl: string) {
    if (articleUrl.length == 0) {
      alert('Please enter a valid URL.');
    } else {
    const fullUrl = `${this.apiUrl}?data=${articleUrl}`;

    this.http.get<{name: string}>(fullUrl)
      .subscribe(data => {
        this.json.next({data})
      });
    }
  }

  // This service can be subscribed to to get the saved JSON each time it updates.
  // Used by DynamicArticle to
  getArticleJson(): Observable<any> {
    return this.json.asObservable();
  }
}