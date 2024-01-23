import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HandleUrlService } from '../Services/handle-url.service';
import { ConfigService } from '../Services/config.service';

@Component({
  selector: 'app-url-submission-form',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './url-submission-form.component.html',
  styleUrl: './url-submission-form.component.css'
})
export class UrlSubmissionFormComponent {
  userUrl : string = "";
  configService: ConfigService = inject(ConfigService)

  OnSubmitUrl(){
    let handleUrl = new HandleUrlService()
    let userUrl : string = handleUrl.OnSubmitUrl(this.userUrl)
    if (userUrl.length == 0) {
      alert('Please enter a valid URL.');
    } else {
      this.configService.getArticle(userUrl)
    }

  }
}
