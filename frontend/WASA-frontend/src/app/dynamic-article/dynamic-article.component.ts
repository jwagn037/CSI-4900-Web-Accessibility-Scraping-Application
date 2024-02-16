import { CommonModule, NgClass } from '@angular/common';
import { Component, Input } from '@angular/core';
import { Subscription } from 'rxjs';
import { ConfigService } from '../Services/config.service';

@Component({
  selector: 'app-dynamic-article',
  standalone: true,
  imports: [CommonModule,
  NgClass],
  templateUrl: './dynamic-article.component.html',
  styleUrl: './dynamic-article.component.css'
})

export class DynamicArticleComponent {
  @Input() themeClass:string = '';
  htmlJson: any;
  htmlList: Array<[string, string]> = [];
  private urlSubscription: Subscription;

  constructor(private configService: ConfigService) {
    // Subscribe to sender component messages
    this.urlSubscription= this.configService.getArticleJson().subscribe
     (message => { // Message contains the data sent from service i.e. resultant API call data
     this.htmlJson = message;
     this.setHtmlList();
     });
    }

  // Prevent memory leaks
  ngOnDestroy() { 
    this.urlSubscription.unsubscribe();
  }

  // Helper for generating dynamic-article.html
  getTagName(tag: string): string {
    const validTags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p'];
    return validTags.includes(tag) ? tag : 'p';
  }

  // Helper for the subscription to ConfigService.
  // Dynamic-article.html needs the JSON content in
  // this specific format (see: var htmlList above)
  private setHtmlList() {
    this.htmlList = [];
    this.htmlJson = JSON.parse(JSON.stringify(this.htmlJson['data']['content']));

    for (var i=0; i<this.htmlJson.length;i++) {
      this.htmlList.push([this.htmlJson[i]['type'],this.htmlJson[i]['text']])
    }
  }
}
