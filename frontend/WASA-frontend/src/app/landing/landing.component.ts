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
  btnTheme: string = "light-btn" // btnTheme and themeClass are defaults

  setLightTheme() {
    this.themeClass = "theme-light";
    this.btnTheme = "light-btn";
    localStorage.setItem('theme-setting','theme-light');
  }

  setDarkTheme() {
    this.themeClass = "theme-dark";
    this.btnTheme = "dark-btn";
    localStorage.setItem('theme-setting','theme-dark');
  }

  setAccess1Theme() {
    this.themeClass = "theme-access1";
    this.btnTheme = "access1-btn";
    localStorage.setItem('theme-setting','theme-access1');
  }

  setAccess2Theme() {
    this.themeClass = "theme-access2";
    this.btnTheme = "access2-btn";
    localStorage.setItem('theme-setting','theme-access2');
  }

  ngOnInit() {
    const darkMode = window.matchMedia("(prefers-color-scheme: dark)");
    const lightMode = window.matchMedia("(prefers-color-scheme: light)");
    const savedThemeSetting = localStorage.getItem('theme-setting');

    if (!Object.is(null,savedThemeSetting)) {
      if (savedThemeSetting == "theme-dark") {
        this.setDarkTheme();
      } else if (savedThemeSetting == "theme-access1") {
        this.setAccess1Theme();
      } else if (savedThemeSetting == "theme-access2") {
        this.setAccess2Theme();
      } else {
        this.setLightTheme();
      }
    } else if (darkMode['matches']) {
      this.setDarkTheme();
    } else if (lightMode['matches']) {
      this.setLightTheme();
    }
  }
}