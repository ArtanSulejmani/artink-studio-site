# Art Ink Studio — поставување на GitHub и Netlify

## 1. Repository

Потврден е пристап за пишување до `ArtanSulejmani/artink-studio-site`.

Repository: `https://github.com/ArtanSulejmani/artink-studio-site`. Не е потребно да создаваш ново repository.

Постави ја СОДРЖИНАТА од папката artink-studio во коренот на repository-то: package.json, netlify.toml, content, public, scripts, src. `dist` е генерирана папка, не е потребна во GitHub. Ако користиш GitHub upload, вклучи ги и скриените .gitignore датотеки преку Git клиент. Овој пакет не содржи credentials.

## 2. Netlify

Import an existing project → GitHub → избери го repository-то. Дај пристап само до потребниот repository.

- Production branch: main
- Build command: npm run build
- Publish directory: dist
- Node: 22 (во netlify.toml)

Првото објавување го создава каталогот. Користи ја адресата што Netlify навистина ќе ја додели. Подоцна може сопствен домен. Не менувај legacy план автоматски. Провери ги реалните кредитни лимити во Usage & billing.

## 3. OAuth за admin

Ова е ОДДЕЛНО од поврзувањето на GitHub со ChatGPT или со Netlify за преземање код.

Во GitHub: Settings → Developer settings → OAuth Apps → New OAuth App.

- Application name: Art Ink Studio CMS
- Homepage URL: точната HTTPS адреса на твојата Netlify страница
- Authorization callback URL: `https://api.netlify.com/auth/done`

Во Netlify: Project configuration → Access & security → OAuth → Authentication Providers → Install provider → GitHub.

Внеси ги Client ID и Client Secret од GitHub директно во Netlify и зачувај. НЕ ги испраќај во разговорот, НЕ ги запишувај во JavaScript или GitHub repository.

Потоа отвори `https://ТВОЈАТА-АДРЕСА/admin/cms/` → Login with GitHub. Треба да се најавиш со профил што има write-пристап до repository-то. Провери ги дозволите пред одобрување. За почеток користи само својот профил; дополнителни уредувачи/private repo contributors може да зависат од Netlify планот.

Официјално упатство: https://docs.netlify.com/manage/security/secure-access-to-sites/oauth-provider-tokens/

## 4. Штедење кредити

1. Отвори `/admin/` → Open content editor.
2. Во Products додади, измени, сокриј или избриши производ. Пополни EN/MK/AL. CMS копчето Save/Publish го зачувува записот во GitHub, не го обновува јавното издание.
3. Додај ги сите фотографии и производи што ти требаат.
4. Кога си подготвен, отвори PUBLISH ALL / ОБЈАВИ СÈ. Зголеми го бројот за 1, на пример 1 → 2, и зачувај.
5. Провери Netlify Deploys и почекај успешно објавување. Сите зачувани промени се објавуваат заедно.

ВАЖНО: „draft“ сам по себе не гарантира заедничко објавување во Decap. Затоа пакетот има сопствен `ignore` услов и release-број. Кога ќе стигне првото успешно Netlify објавување, провери: измени опис → нема production deploy; зголеми release → има само едно. Ако не е така, стопирај ги честите промени и провери дали netlify.toml е во коренот.

Manual deploy и build hooks може да го заобиколат условот. Не ги поставувај како автоматски повик при секое зачувување. Deploy previews и други проекти исто можат да трошат сообраќај. Бесплатно не значи неограничено.

## 5. Пред јавно пуштање

- Дополни правно име и адреса во Studio settings; потврди ја политиката за чување пораки со лицето што го води работењето.
- Потврди право за користење на фотографиите од добавувачите. Наведените производи се почетен избор, не потврдена залиха.
- Провери ги преводите, артиклите, материјалите и контактите.
- Логото е привремен типографски знак; замени го со официјално лого ако го имаш.
- Тестирај quote → mail app и Gmail, WhatsApp, телефон, јазични врски и admin login.
- Провери canonical/hreflang/sitemap на вистинскиот домен и отстрани preview noindex преку правилната URL конфигурација (не со рачно бришење од HTML).
- Политиката е работен нацрт, потребна е проверка за конкретното правно лице и деловни практики.

## 6. Нови категории

Почетните категории се textiles, drinkware, accessories, gifts. Производите се целосно уредливи преку admin. За нова категорија треба да се додаде превод во `src/i18n.mjs` (categories и categoryCopy); потоа генераторот автоматски ја додава во филтрите, lookbook и CMS изборот. Свадбени покани имаат посебен дел за барање понуда; реални модели/фотографии може да се додадат по доставување.
