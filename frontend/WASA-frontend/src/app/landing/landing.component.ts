import { Component } from '@angular/core';
import { DynamicArticleComponent } from '../dynamic-article/dynamic-article.component';
import { UrlSubmissionFormComponent } from '../url-submission-form/url-submission-form.component';
import { NgClass } from '@angular/common';

@Component({
  selector: 'app-landing',
  standalone: true,
  imports: [
    DynamicArticleComponent,
    UrlSubmissionFormComponent,
    NgClass
  ],
  templateUrl: './landing.component.html',
  styleUrl: './landing.component.css'
})
export class LandingComponent {
  themeClass: string = "theme-light"

  setLightTheme() {
    this.themeClass = "theme-light"
  }

  setDarkTheme() {
    this.themeClass = "theme-dark"
  }

  setAccess1Theme() {
    this.themeClass = "theme-access1"
  }

  setAccess2Theme() {
    this.themeClass = "theme-access2"
  }

}