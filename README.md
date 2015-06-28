# atlaser
Usage: `python atlaser.py <directory> <layer name> <output path>`

Takes every layer called &lt;layer name&gt; inside every .psd file within &lt;directory&gt;
and combines it into a single .png file at &lt;output path&gt;.

Currently assumes every file is the same size.

Also generates a .info file that contains the index offsets for the first frames of each
different file name.
