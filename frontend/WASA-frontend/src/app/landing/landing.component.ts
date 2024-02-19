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
  themeClass: string = "theme-light" // UrlSubmissionForm, DynamicArticleComponent take this as an input to use in their HTML

  setLightTheme() {
    this.themeClass = "theme-light";
    localStorage.setItem('theme-setting','theme-light');
  }

  setDarkTheme() {
    this.themeClass = "theme-dark";
    localStorage.setItem('theme-setting','theme-dark');
  }

  setAccess1Theme() {
    this.themeClass = "theme-access1";
    localStorage.setItem('theme-setting','theme-access1');
  }

  setAccess2Theme() {
    this.themeClass = "theme-access2";
    localStorage.setItem('theme-setting','theme-access2');
  }

  ngOnInit() {
    const darkMode = window.matchMedia("(prefers-color-scheme: dark)");
    const lightMode = window.matchMedia("(prefers-color-scheme: light)");
    const savedThemeSetting = localStorage.getItem('theme-setting');

    if (!Object.is(null,savedThemeSetting)) {
      this.themeClass = String(savedThemeSetting);
    } else if (darkMode['matches']) {
      this.themeClass = "theme-dark";
    } else if (lightMode['matches']) {
      this.themeClass = "theme-light";
    } else {
      this.themeClass = "theme-light";
    }
  }

}