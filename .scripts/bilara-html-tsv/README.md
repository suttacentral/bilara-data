### Overview
See [Sanskrit text preparation](https://github.com/suttacentral/bilara-data/wiki/Sanskrit-text-preparation)

### Installation
```
git clone https://github.com/sc-voice/bilara-html-tsv
cd bilara-html-tsv
npm install
```

Verify instalation by running the `html-tsv.js` script to display
command options:

```
./scripts/html-tsv --help
```

### Convert an HTML file

To convert and save an html file to a TSV file, 
[redirect the terminal output to a file](https://askubuntu.com/questions/420981/how-do-i-save-terminal-output-to-a-file)
```

./scripts/html-tsv html/sf36.html > ../bilara-io/tsv/sf36.tsv

```

The `local` folder is ignored by Git and can be used as a repository-local 
playground.

For testing HTML files, you can use `ugly.css`, add the following to the HTML document head:

```
<link rel="stylesheet" href="ugly.css">
```

This aims to style every element is a distinct and ugly way so you can easily spot differences. Add or change anything, it is meant to be ugly!

### Segment numbering
Default numbering is by paragraph and segment number. 
Each `<p>` encountered increments the paragraph number.
The initial paragraph number is zero.
For example, `test/data/test-sf276-dummy.html` is numbered as:

```
segment_id	html	root	comment
sf276:0.1	<article id='sf276'><header><h1>{}</h1></header>	Candrasūtra	
sf276:1.1	<p>{}	evaṃ mayā śrutam	
sf276:1.2	{}</p>	ekasama<supplied>yaṃ bhagavāñ</supplied> śrāvastyāṃ viharati jet<supplied>a</supplied>v<supplied>a</supplied>n<supplied>a</supplied> anāthapiṇḍad<supplied>ā</supplied>r<supplied>ā</supplied>m<supplied>e /</supplied>	
sf276:2.1	<p>{}</p>	tena khalu samayena rāhuṇā asurendreṇa sarvaṃ candramaṇḍalam āvṛtam* <supplied>/</supplied>	
sf276:3.1	<p>{}</p>	<supplied>atha</supplied> yā devatā tasmiṃ<supplied>ś</supplied> candramaṇḍala adhyuṣitā sā bhītā trast<supplied>ā</supplied> saṃvignā āhṛṣṭaromakūpā yena bhagavāṃs teno<supplied>pajagāma /</supplied> upetya bha<supplied>ga</supplied>v<supplied>a</supplied>tpādau śirasā <supplied>vanditvaikāṃ</supplied>te 'sthād ekāntasthitā sā devatā tasyāṃ velāyāṃ gāthā babhāṣe //	
sf276:4.1	<p>{}	buddhavīra namas te 'stu vipramuktāya sarvataḥ	Ed. bhitā but MS reads bhītā
sf276:4.2	{}</p><blockquote class='gatha'>	saṃbādhapratipannāsmi tasya me śaraṇaṃ bhava :	Ed. buddha vīra
sf276:5.1	<p><span class='verse-line'>{}</span>	arhantaṃ sugataṃ loke candramāḥ śaraṇaṃ gataḥ	
sf276:5.2	<span class='verse-line'>{}</span></p></blockquote>	<span class='verse-line'>rāhoś candramasaṃ muñca buddhā lokānukampakāḥ //	
sf276:6.1	<p>{}</p>	bhagavān āha //	
sf276:7.1	<p>{}	tamonudaṃ taṃ nabhasi prabhākaraṃ virocanaṃ śukla<supplied>v</supplied>iśuddhavarcasam*	
sf276:7.2	{}</p>	rāho ś<supplied>a</supplied>śāṅkaṃ grasa māntarīkṣe praj<supplied>ā</supplied>pr<supplied>a</supplied>dīpaṃ drutam utsṛjainam* //	
sf276:8.1	<p>{}	atha rāhuṇā as<supplied>u</supplied>rendreṇa tvaritatvaritaṃ candramaṇḍalam utsṛṣṭam* ⟨/⟩	
sf276:8.2	{}	tataḥ sa<supplied>ṃ</supplied>tvaramāṇo 'sau rāhuś candram avāsṛ<supplied>jat*</supplied>	
sf276:8.3	{}</p>	<supplied>saṃsvinnagātro vya</supplied>thitaḥ saṃbhr<supplied>ānta āturo ya</supplied>thā //	
sf276:9.1	<p>{}</p>	adrākṣīd baḍir vairocano <supplied>rāhuṇā</supplied> asurendreṇa tvaritatvaritaṃ candr<supplied>a</supplied>maṇḍala<supplied>m utsṛṣṭam* / dṛṣṭvā ca baḍi</supplied>r gāthāṃ babhāṣe //	
sf276:10.1	<p>{}	ki<supplied>ṃ</supplied> nu sa<supplied>ṃ</supplied>tv<supplied>aramāṇas</supplied> tv<supplied>aṃ</supplied> rāhuś candraṃ vimuñcasi ·	
sf276:10.2	{}</p>	saṃsvinnagātro vyathitaḥ saṃ<supplied>bhrānta āturo yathā</supplied> <supplied>//</supplied>	Cf. Pelliot Sanskrit bleu 449 Ac: /// ro yathā //
sf276:11.1	<p>{}</p>	<supplied>rāhur avocat* //</supplied>	
sf276:12.1	<p>{}	<supplied>sa</supplied>ptadhā me sphalen mūrdhā <supplied>jīvan na sukha</supplied>m āp<supplied>nu</supplied>yāṃ	
sf276:12.2	{}</p>	ta<supplied>tra buddh</supplied>ābhigītena muñceyaṃ śaśinaṃ na cet*	Cf. Pelliot Sanskrit bleu 449 Ac: rāhu prāha // saptadhā me sphal[e] mūrdhā
sf276:13.1	<p>{}	<supplied>baḍir vairocano 'vocat* /</supplied>	
sf276:13.2	{}	x x x x x - - - x x x x madarśi<supplied>nāṃ</supplied>	
sf276:13.3	{}</p>	<supplied>teṣāṃ gāthābhigītena rāhuś candraṃ vimuñcati //</supplied>	Cf. Pelliot Sanskrit bleu 449 Ad: + + + + + .. .. .. .. .. .. .. (bh)i(g)itena muñce
sf276:14.1	<p>{}</p></article>	<supplied>candrasūtraṃ samāptam* //</supplied>	
```

#### Segment numbering by example
Segment numbers can be overridden with the segment `id='...'` attribute.
Subsequent numbers will automatically use the new segment numbering basis.
This _segment numbering by example_ provides the greatest flexibility of
segment numbering since it makes no assumptions about HTML
structure other than paragraphs.

For example, let's look at the Donut Sutta:
```
<!DOCTYPE html>
<html>
<head>
<title>DONUTS</title>
</head>
<body>
<article id='donuts'><header><h1><segment'>donuts A</segment></h1></header>
<p>
  <segment id='chocolate:1.1'><root>donuts B</root></segment>
  <segment><root>donuts C</root></segment>
</p>
<p>
  <segment id='glazed:1.1'><root>donuts D</root></segment>
  <segment><root>donuts E</root></segment>
</p>
</article>
</body>
</html>
```

The Donut Sutta will be numbered as

```
segment_id	html	root	comment
donuts:0.1	<article id='donuts'><header><h1>{}</h1></header>	donuts A	
chocolate:1.1	<p>  {}	donuts B	
chocolate:1.2	{}</p>	donuts C	
glazed:1.1	<p>  {}	donuts D	
glazed:1.2	{}</p></article>	donuts E	
```

