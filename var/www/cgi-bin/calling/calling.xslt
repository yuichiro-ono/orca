<?xml version="1.0" encoding="UTF-8" ?>

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
   <xsl:output method="html" encoding="UTF-8"/>

	<xsl:variable name="my_uri">http://192.168.0.3/cgi-bin/reservelist.cgi</xsl:variable>

	<xsl:template match="/">
		<xsl:apply-templates/>
 	</xsl:template>

	<xsl:template match="acceptlstres">
		<html>
		<head>
			<meta charset="utf-8" />
			<title>呼び出しリスト</title>
			<link rel="stylesheet" href="/calling.css" />
		</head>
		<body>
			<div class="title">診療案内</div>
			<h1>&gt; 次の番号の方は間もなく診察です</h1>
			<table class="frame">
				<tr>
					<xsl:apply-templates select="Acceptlst_Information/Acceptlst_Information_child" mode="soon" />
				</tr>
			</table>

			<hr />
			<h1>&gt; 以下の番号の方は，しばらくお待ちください．</h1>
			<table class="frame">
				<tr>
				<xsl:apply-templates select="Acceptlst_Information/Acceptlst_Information_child" mode="later" />
				</tr>
			</table>
		</body>
		</html>
	</xsl:template>

	<xsl:template match="Acceptlst_Information/Acceptlst_Information_child" mode="soon">
		<!-- xsl:variable name="pos"><xsl:value-of select="position()" /> </xsl:variable>  -->
		<xsl:if test="position() = 1 ">
			<td>
				<table class="numbers_next">
					<tr><td class="number_cell_next"><xsl:value-of select="Patient_Information/Patient_ID" /> </td></tr>
				</table>
			</td>
		</xsl:if>
	</xsl:template>

	<xsl:template match="Acceptlst_Information/Acceptlst_Information_child" mode="later">
		<xsl:if test="(position() &gt; 1) and (position() &lt; 4) ">
			<td>
				<table class="numbers">
					<tr><td class="number_cell"><xsl:value-of select="Patient_Information/Patient_ID" /> </td></tr>
				</table>
			</td>
		</xsl:if>
	</xsl:template>

</xsl:stylesheet>

