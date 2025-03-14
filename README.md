# DefectDojo

<table>
    <tr styl="margin: 0; position: absolute; top: 50%; -ms-transform: translateY(-50%); transform: translateY(-50%);">
        <th>
            <a href="https://opensourcesecurityindex.io/" target="_blank" rel="noopener">
                <img style="width: 282px; height: 56px" src="https://opensourcesecurityindex.io/badge.svg"
                alt="Open Source Security Index - Fastest Growing Open Source Security Projects" width="282" height="56" />
            </a>
        </th>
        <th>
            <p>
                <a href="https://www.owasp.org/index.php/OWASP_DefectDojo_Project"><img src="https://img.shields.io/badge/owasp-flagship%20project-orange.svg" alt="OWASP Flagship"></a>
                <a href="https://github.com/DefectDojo/django-DefectDojo/releases/latest"><img src="https://img.shields.io/github/release/DefectDojo/django-DefectDojo.svg" alt="GitHub release"></a>
                <a href="https://www.youtube.com/channel/UCWw9qzqptiIvTqSqhOFuCuQ"><img src="https://img.shields.io/badge/youtube-subscribe-%23c4302b.svg" alt="YouTube Subscribe"></a>
                <a href="https://twitter.com/defectdojo/"><img src="https://img.shields.io/twitter/follow/defectdojo.svg?style=social&amp;label=Follow" alt="Twitter Follow"></a>
            </p>
            <p>
                <a href="https://github.com/DefectDojo/django-DefectDojo/actions"><img src="https://github.com/DefectDojo/django-DefectDojo/actions/workflows/unit-tests.yml/badge.svg?branch=master" alt="Unit Tests"></a>
                <a href="https://github.com/DefectDojo/django-DefectDojo/actions"><img src="https://github.com/DefectDojo/django-DefectDojo/actions/workflows/integration-tests.yml/badge.svg?branch=master" alt="Integration Tests"></a>
                <a href="https://bestpractices.coreinfrastructure.org/projects/2098"><img src="https://bestpractices.coreinfrastructure.org/projects/2098/badge" alt="CII Best Practices"></a>
            </p>
        </th>
    </tr>
 </table>

![Screenshot of DefectDojo](https://raw.githubusercontent.com/DefectDojo/django-DefectDojo/dev/docs/static/images/screenshot1.png)

[DefectDojo](https://www.defectdojo.com/) is a DevSecOps, ASPM (application security posture management), and
vulnerability management tool.  DefectDojo orchestrates end-to-end security testing, vulnerability tracking,
deduplication, remediation, and reporting.

## Demo

Get a free trial of the Pro Edition [here](https://cloud.defectdojo.com/accounts/login/?next=/) or by reaching out to us at hello@defectdojo.com.

Alternatively, try out the open-source OWASP Edition on our demo server at [demo.defectdojo.org](https://demo.defectdojo.org)

Log in with username `admin` and password `1Defectdojo@demo#appsec`. Please note that the demo is publicly accessible
and regularly reset. Do not put sensitive data in the demo.

## How to get DefectDojo
### Pro
1. Get the best version of DefectDojo with a trial at [cloud.defectdojo.com](https://cloud.defectdojo.com/accounts/login/?next=/)
2. Buy through [AWS and get instant access](https://aws.amazon.com/marketplace/pp/prodview-stklscizixsra)
3. Talk to us by emailing hello@defectdojo.com

### Open-Source OWASP Edition

1. **Quick Start via Docker Compose**

** From July 2023 Compose V1 [stopped receiving updates](https://docs.docker.com/compose/reference/).

** Compose V2 integrates compose functions into the Docker platform, continuing to support most of the previous
** docker-compose features and flags. You can run Compose V2 by replacing the hyphen (-) with a space, using
** `docker compose` instead of `docker-compose`.</p>

```sh
# Clone the project
git clone https://github.com/DefectDojo/django-DefectDojo
cd django-DefectDojo

# Building Docker images
./dc-build.sh

# Run the application (for other profiles besides postgres-redis see  
# https://github.com/DefectDojo/django-DefectDojo/blob/dev/readme-docs/DOCKER.md)
./dc-up-d.sh postgres-redis

# Obtain admin credentials. The initializer can take up to 3 minutes to run.
# Use docker compose logs -f initializer to track its progress.
docker compose logs initializer | grep "Admin password:"
```
Navigate to `http://localhost:8080` to see your new instance!

2. [Other Installation Options](https://docs.defectdojo.com/en/open_source/installation/installation/)

## Documentation

* [Official Docs](https://documentation.defectdojo.com/)
    * [Docs for our `dev` branch](https://documentation.defectdojo.com/dev/)
* [REST APIs](https://documentation.defectdojo.com/integrations/api-v2-docs/)
* [Client APIs and Wrappers](https://documentation.defectdojo.com/integrations/api-v2-docs/#clients--api-wrappers)
* Authentication options:
    * [OAuth2/SAML2](https://documentation.defectdojo.com/integrations/social-authentication/)
    * [LDAP](https://documentation.defectdojo.com/integrations/ldap-authentication/)
* [Supported tools](https://documentation.defectdojo.com/integrations/parsers/)

## Community, Getting Involved, and Updates

[<img src="https://raw.githubusercontent.com/DefectDojo/django-DefectDojo/dev/docs/static/images/slack-logo-icon.png" alt="Slack" height="50"/>](https://owasp.org/slack/invite)
[<img src="https://raw.githubusercontent.com/DefectDojo/django-DefectDojo/dev/docs/static/images/Linkedin-logo-icon-png.png" alt="LinkedIn" height="50"/>](https://www.linkedin.com/company/defectdojo)
[<img src="https://raw.githubusercontent.com/DefectDojo/django-DefectDojo/dev/docs/static/images/Twitter_Logo.png" alt="Twitter" height="50"/>](https://twitter.com/defectdojo)
[<img src="https://raw.githubusercontent.com/DefectDojo/django-DefectDojo/dev/docs/static/images/YouTube-Emblem.png" alt="Youtube" height="50"/>](https://www.youtube.com/channel/UCWw9qzqptiIvTqSqhOFuCuQ)

[Join the OWASP Slack community](https://owasp.org/slack/invite) and participate in the discussion! You can find us in
our channel there, [#defectdojo](https://owasp.slack.com/channels/defectdojo). Follow DefectDojo on
[Twitter](https://twitter.com/defectdojo), [LinkedIn](https://www.linkedin.com/company/defectdojo), and
[YouTube](https://www.youtube.com/channel/UCWw9qzqptiIvTqSqhOFuCuQ) for project updates!

## Contributing

Please see our [contributing guidelines](readme-docs/CONTRIBUTING.md) for more
information. Check out our latest update on v3 [here](https://github.com/DefectDojo/django-DefectDojo/discussions/8974).

## Pro Edition
[Upgrade to DefectDojo Pro](https://www.defectdojo.com/pricing) today to take your DevSecOps to 11. DefectDojo Pro is
designed to meet you wherever you are on your security journey and help you scale, with enhanced dashboards, additional
smart features, tunable deduplication, and support from DevSecOps experts.

Alternatively, for information please email info@defectdojo.com

## About Us

DefectDojo is maintained by:
* Greg Anderson ([@devGregA](https://github.com/devgrega) | [LinkedIn](https://www.linkedin.com/in/g-anderson/))
* Matt Tesauro ([@mtesauro](https://github.com/mtesauro) | [LinkedIn](https://www.linkedin.com/in/matttesauro/) |
  [@matt_tesauro](https://twitter.com/matt_tesauro))

Core Moderators can help you with pull requests or feedback on dev ideas:
* Cody Maffucci ([@Maffooch](https://github.com/maffooch) | [LinkedIn](https://www.linkedin.com/in/cody-maffucci))

Moderators can help you with pull requests or feedback on dev ideas:
* Damien Carol ([@damiencarol](https://github.com/damiencarol) | [LinkedIn](https://www.linkedin.com/in/damien-carol/))
* Jannik Jürgens ([@alles-klar](https://github.com/alles-klar))
* Dubravko Sever ([@dsever](https://github.com/dsever))
* Charles Neill ([@cneill](https://github.com/cneill) | [@ccneill](https://twitter.com/ccneill))
* Jay Paz ([@jjpaz](https://twitter.com/jjpaz))
* Blake Owens ([@blakeaowens](https://github.com/blakeaowens))

## Hall of Fame

* Valentijn Scholten ([@valentijnscholten](https://github.com/valentijnscholten) |
  [Sponsor](https://github.com/sponsors/valentijnscholten) |
  [LinkedIn](https://www.linkedin.com/in/valentijn-scholten/)) - Valentijn served as a core moderator for 3 years.
  Valentijn's contributions were numerous and extensive. He overhauled, improved, and optimized many parts of the
  codebase. He consistently fielded questions, provided feedback on pull requests, and provided a helping hand wherever
  it was needed.
* Fred Blaise ([@madchap](https://github.com/madchap) | [LinkedIn](https://www.linkedin.com/in/fredblaise/)) - Fred
  served as a core moderator during a critical time for DefectDojo. He contributed code, helped the team stay organized,
  and architected important policies and procedures.
* Aaron Weaver ([@aaronweaver](https://github.com/aaronweaver) | [LinkedIn](https://www.linkedin.com/in/aweaver/)) -
  Aaron has been a long time contributor and user of DefectDojo. He did the second major UI overhaul and his
  contributions include automation enhancements, CI/CD engagements, increased metadata at the product level, and many
  more.

## Security

Please report Security issues via our [disclosure policy](readme-docs/SECURITY.md).

## License

DefectDojo is licensed under the [BSD 3-Clause License](LICENSE.md)
