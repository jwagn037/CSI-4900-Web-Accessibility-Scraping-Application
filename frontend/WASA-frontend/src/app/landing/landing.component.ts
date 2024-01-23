import { Component } from '@angular/core';
import { DynamicArticleComponent } from '../dynamic-article/dynamic-article.component';
import { UrlSubmissionFormComponent } from '../url-submission-form/url-submission-form.component';

@Component({
  selector: 'app-landing',
  standalone: true,
  imports: [
    DynamicArticleComponent,
    UrlSubmissionFormComponent
  ],
  templateUrl: './landing.component.html',
  styleUrl: './landing.component.css'
})
export class LandingComponent {
  

}