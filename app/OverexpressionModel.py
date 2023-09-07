from app.Base import BaseModel
from app.settings import *
from Bio.Blast import NCBIXML

class Overexpression(BaseModel):
	"""Class for overexpression searches."""
	def __init__(self, input_type, loose, input_sequence, xml_file, working_directory, local_database=False, include_nudge=False):
		self.input_type = input_type
		self.loose = loose
		self.input_sequence = input_sequence
		self.xml_file = xml_file
		self.output = {}
		self.working_directory = working_directory

		self.local_database = local_database
		self.data = data_path

		self.include_nudge = include_nudge

		if self.local_database:
			self.db = LOCAL_DATABASE
			self.data = LOCAL_DATABASE

	def __repr__(self):
		"""Returns Overexpression class full object."""
		return "Overexpression({}".format(self.__dict__)

	def run(self):
		"""Runs overexpression search."""
		blastResults = {}
		perfect = {}
		strict = {}
		loose = {}
		predicted_genes_dict = {}
		# predicted_genes_dict_protein = {}
		submitted_proteins_dict = {}

		if self.input_type == "contig":
			predicted_genes_dict = self.get_orf_dna_sequence(self.input_sequence,self.input_type)
			# predicted_genes_dict_protein = self.get_orf_protein_sequence(self.input_sequence,self.input_type)

		if self.input_type == "protein":
			submitted_proteins_dict = self.get_submitted_protein_sequence(self.input_sequence)

		with open(os.path.join(self.data,"card.json")) as json_file:
			json_data = json.load(json_file)

		with open(self.xml_file, 'r') as result_handle:
			blast_records = NCBIXML.parse(result_handle)
			for blast_record in blast_records:
				perfect = {}
				strict = {}
				loose = {}

				for alignment in blast_record.alignments:

					alignTitle = alignment.title
					orfInfo = blast_record.query.encode('ascii','replace')

					c = 0
					barc = 0
					for eachc in orfInfo:
						if barc >= 6:
							break
						elif eachc == '|':
							barc += 1
							c += 1
						else:
							c += 1
					orffrom = orfInfo[c:]

					modelTypeID = self.extract_nth_bar(alignTitle, 0)

					if modelTypeID == 41091:
						# logger.debug("modelTypeID: {} ".format(modelTypeID))

						spacepos = alignTitle.index(' ')
						hitid = alignTitle[0:spacepos]
						hitid = hitid.encode('ascii','replace')
						modelDescrpt =alignTitle[alignTitle.index(' ')+1:]
						underscoreinMD = modelDescrpt.index('_')
						modelID = modelDescrpt[0:underscoreinMD]
						seqinModel = modelDescrpt[underscoreinMD+1: modelDescrpt.index(' ')]

						init = 0
						snp = self.extract_nth_bar(alignTitle, 2)
						snp = snp.split(',')
						snpL = []
						snpdictlist = []
						temp = ""

						pass_bitscore = "{}".format(self.extract_nth_bar(alignment.title, 1))
						pass_evalue = "{}".format("n/a")

						# logger.debug("pass_evalue: {}".format(pass_evalue))
						# logger.debug("pass_bitscore: {}".format(pass_bitscore))

						for eachsnp in snp:
							"""Creates a SNP dictionary."""
							snpdictlist.append({"original": eachsnp[0], "change": eachsnp[-1], "position": eachsnp[1:-1]})

						for hsp in alignment.hsps:
							querySeq = hsp.query.replace('-', '')
							realQueryLength = len(querySeq)
							# card_sequence = str(json_data[modelID]["model_sequences"]["sequence"][seqinModel]["protein_sequence"]["sequence"])
							try:
								card_sequence = str(json_data[modelID]["model_sequences"]["sequence"][seqinModel]["protein_sequence"]["sequence"])
							except Exception as e:
								logger.warning("Exception : {} -> {} -> Model({}) missing in database. Please generate new database.".format(type(e), e, modelID))
							else:
								card_sequence = ""

							orf_protein_sequence = ""

							if predicted_genes_dict:
								if orfInfo.strip() in predicted_genes_dict.keys():
									orf_protein_sequence = str(Seq(predicted_genes_dict[orfInfo.decode()]).translate(table=11)).strip("*")
								else:
									orf_protein_sequence = str(Seq(predicted_genes_dict[orfInfo.decode()[:orfInfo.decode().index(' # ')]]).translate(table=11)).strip("*")

							# if predicted_genes_dict_protein:
							# 	if orfInfo.strip() in predicted_genes_dict_protein.keys():
							# 		orf_protein_sequence = predicted_genes_dict_protein[orfInfo.decode()].strip("*")
							# 	else:
							# 		orf_protein_sequence = predicted_genes_dict_protein[orfInfo.decode()[:orfInfo.decode().index(' # ')]].strip("*")

							if submitted_proteins_dict:
								orf_protein_sequence = str(submitted_proteins_dict[orfInfo.decode().split(" ")[0]])

							try:
								if card_sequence.upper() == orf_protein_sequence.upper():
									"""Perfect hits."""
									# logger.debug("Perfect hits")
									ppinsidedict = {}
									ppinsidedict["type_match"] = "Perfect"
									ppinsidedict["model_id"] = modelID
									ppinsidedict["orf_strand"] = self.extract_nth_bar(orfInfo, 0)
									ppinsidedict["orf_start"] = self.extract_nth_bar(orfInfo, 1)
									ppinsidedict["orf_end"] = self.extract_nth_bar(orfInfo, 2)
									ppinsidedict["orf_from"] = orffrom.decode()
									ppinsidedict["model_name"] = json_data[modelID]["model_name"]
									ppinsidedict["model_type"] = json_data[modelID]["model_type"]
									ppinsidedict["model_type_id"] = modelTypeID
									ppinsidedict["pass_evalue"] = pass_evalue
									ppinsidedict["pass_bitscore"] = pass_bitscore
									ppinsidedict["ARO_accession"] = json_data[modelID]["ARO_accession"]
									ppinsidedict["ARO_name"] = json_data[modelID]["ARO_name"]
									ppinsidedict["ARO_category"] = json_data[modelID]["ARO_category"]
									ppinsidedict["evalue"] = hsp.expect
									ppinsidedict["bit_score"] = hsp.bits
									ppinsidedict["max_identities"] = hsp.identities
									ppinsidedict["cvterm_id"] = json_data[modelID]["model_sequences"]["sequence"][seqinModel]["NCBI_taxonomy"]["NCBI_taxonomy_cvterm_id"]
									ppinsidedict["query"] = hsp.query
									ppinsidedict["match"] = hsp.match
									ppinsidedict["sequence_from_db"] = hsp.sbjct
									ppinsidedict["sequence_from_broadstreet"] = json_data[modelID]["model_sequences"]["sequence"][seqinModel]["protein_sequence"]["sequence"]
									ppinsidedict["dna_sequence_from_broadstreet"] = json_data[modelID]["model_sequences"]["sequence"][seqinModel]["dna_sequence"]["sequence"]
									if "partial" in json_data[modelID]["model_sequences"]["sequence"][seqinModel]["dna_sequence"].keys():
										ppinsidedict["partial"] = json_data[modelID]["model_sequences"]["sequence"][seqinModel]["dna_sequence"]["partial"]
									else:
										ppinsidedict["partial"] = "0"

									if self.input_type == 'contig':
										ppinsidedict["query_start"] = self.extract_nth_hash(orfInfo.decode(), 1) + (hsp.query_start - 1)*3
										ppinsidedict["query_end"] = self.extract_nth_hash(orfInfo.decode(), 1) + (hsp.query_start - 1)*3 + realQueryLength*3 - 1
										ppinsidedict["orf_strand"] = self.extract_nth_hash(orfInfo.decode(), 3)
										ppinsidedict["orf_start"] = self.extract_nth_hash(orfInfo.decode(), 1)
										ppinsidedict["orf_end"] = self.extract_nth_hash(orfInfo.decode(), 2)
										ppinsidedict["orf_from"] = self.extract_nth_hash(orfInfo.decode(), 0).rstrip()
										ppinsidedict["hit_start"] = (hsp.sbjct_start-1)*3
										ppinsidedict["hit_end"] = (hsp.sbjct_end)*3


										if orfInfo.decode().split(' # ')[0] in predicted_genes_dict:
											ppinsidedict["orf_dna_sequence"] = predicted_genes_dict[orfInfo.decode().split(' # ')[0]]
											ppinsidedict["orf_prot_sequence"] = str(Seq(predicted_genes_dict[orfInfo.decode().split(' # ')[0]]).translate(table=11)).strip("*")
											# ppinsidedict["orf_prot_sequence"] = orf_protein_sequence
										else:
											ppinsidedict["orf_dna_sequence"] = ""
											ppinsidedict["orf_prot_sequence"] = ""

									elif self.input_type == 'protein':
										ppinsidedict["query_start"] = hsp.query_start
										ppinsidedict["query_end"] = hsp.query_start + realQueryLength
										ppinsidedict["query_from"] = blast_record.query
										ppinsidedict["orf_prot_sequence"] = orf_protein_sequence
										ppinsidedict["hit_start"] = ""
										ppinsidedict["hit_end"] = ""

									elif self.input_type == 'read':
										pass

									ppinsidedict["perc_identity"] = float(format(float(ppinsidedict["max_identities"]*100) / len(ppinsidedict["query"]),'.2f'))
									perfect["{}|hsp_num:{}".format(hitid.decode(),init)] = ppinsidedict
									init += 1

								elif float(hsp.bits) >= float(pass_bitscore):
									snp_counter = 0
									for eachs in snpdictlist:
										"""SNP detection for strict hit."""
										pos = eachs["position"]
										ori = eachs["original"]
										chan = eachs["change"]

										if hsp.sbjct_start < int(pos) and (hsp.sbjct_start + realQueryLength) > int(pos):
											"""Checks if there is a mutation."""
											# logger.debug("Mutation check")

											qry = int(pos) - hsp.sbjct_start + self.find_num_dash(hsp.sbjct, (int(pos) - hsp.sbjct_start))
											sbj = int(pos) - hsp.sbjct_start + self.find_num_dash(hsp.sbjct, (int(pos) - hsp.sbjct_start))

											if hsp.query[qry] == chan:
												# logger.debug("Mutation detected")
												snp_counter+=1
												sinsidedict = {}
												sinsidedict["type_match"] = "Strict"
												sinsidedict["orf_strand"] = self.extract_nth_bar(orfInfo.decode(), 0)
												sinsidedict["orf_start"] = self.extract_nth_bar(orfInfo.decode(), 1)
												sinsidedict["orf_end"] = self.extract_nth_bar(orfInfo.decode(), 2)
												sinsidedict["orf_from"] = orffrom.decode()
												sinsidedict["model_name"] = json_data[modelID]["model_name"]
												sinsidedict["model_type"] = json_data[modelID]["model_type"]
												sinsidedict["model_type_id"] = modelTypeID
												sinsidedict["model_id"] = modelID
												sinsidedict["snp"] = eachs
												sinsidedict["pass_evalue"] = pass_evalue
												sinsidedict["pass_bitscore"] = pass_bitscore
												sinsidedict["ARO_accession"] = json_data[modelID]["ARO_accession"]
												sinsidedict["ARO_name"] = json_data[modelID]["ARO_name"]
												sinsidedict["ARO_category"] = json_data[modelID]["ARO_category"]
												sinsidedict["evalue"] = hsp.expect
												sinsidedict["bit_score"] = hsp.bits
												sinsidedict["max_identities"] = hsp.identities
												sinsidedict["cvterm_id"] = json_data[modelID]["model_sequences"]["sequence"][seqinModel]["NCBI_taxonomy"]["NCBI_taxonomy_cvterm_id"]
												sinsidedict["query"] = hsp.query
												sinsidedict["match"] = hsp.match
												sinsidedict["sequence_from_db"] = hsp.sbjct
												sinsidedict["sequence_from_broadstreet"] = json_data[modelID]["model_sequences"]["sequence"][seqinModel]["protein_sequence"]["sequence"]
												sinsidedict["dna_sequence_from_broadstreet"] = json_data[modelID]["model_sequences"]["sequence"][seqinModel]["dna_sequence"]["sequence"]
												if "partial" in json_data[modelID]["model_sequences"]["sequence"][seqinModel]["dna_sequence"].keys():
													sinsidedict["partial"] = json_data[modelID]["model_sequences"]["sequence"][seqinModel]["dna_sequence"]["partial"]
												else:
													sinsidedict["partial"] = "0"

												if self.input_type == 'contig':
													sinsidedict["query_start"] = self.extract_nth_hash(orfInfo.decode(), 1) + (hsp.query_start - 1)*3
													sinsidedict["query_end"] = self.extract_nth_hash(orfInfo.decode(), 1) + (hsp.query_start - 1)*3 + realQueryLength*3 - 1
													sinsidedict["orf_strand"] = self.extract_nth_hash(orfInfo.decode(), 3)
													sinsidedict["orf_start"] = self.extract_nth_hash(orfInfo.decode(), 1)
													sinsidedict["orf_end"] = self.extract_nth_hash(orfInfo.decode(), 2)
													sinsidedict["orf_from"] = self.extract_nth_hash(orfInfo.decode(), 0).rstrip()
													sinsidedict["hit_start"] = (hsp.sbjct_start-1)*3
													sinsidedict["hit_end"] = (hsp.sbjct_end)*3

													if orfInfo.decode().split(' # ')[0] in predicted_genes_dict:
														sinsidedict["orf_dna_sequence"] = predicted_genes_dict[orfInfo.decode().split(' # ')[0]]
														sinsidedict["orf_prot_sequence"] = str(Seq(predicted_genes_dict[orfInfo.decode().split(' # ')[0]]).translate(table=11)).strip("*")
														# sinsidedict["orf_prot_sequence"] = orf_protein_sequence
													else:
														sinsidedict["orf_dna_sequence"] = ""
														sinsidedict["orf_prot_sequence"] = ""

												elif self.input_type == 'protein':
													sinsidedict["query_start"] = hsp.query_start
													sinsidedict["query_end"] = hsp.query_start + realQueryLength
													sinsidedict["query_from"] = blast_record.query
													sinsidedict["orf_prot_sequence"] = orf_protein_sequence
													sinsidedict["hit_start"] = ""
													sinsidedict["hit_end"] = ""

												elif self.input_type == 'read':
													pass

												sinsidedict["perc_identity"] = float(format(float(sinsidedict["max_identities"]*100) / len(sinsidedict["query"]),'.2f'))
												strict["{}|hsp_num:{}".format(hitid.decode(),init)] = sinsidedict
												init += 1

									else:
										if snp_counter == 0:
											"""If no SNP detected in strict hit."""
											# logger.debug("Strict hits - no SNP")
											insidedict = {}
											insidedict["type_match"] = "Strict"
											insidedict["orf_strand"] = self.extract_nth_bar(orfInfo.decode(), 0)
											insidedict["orf_start"] = self.extract_nth_bar(orfInfo.decode(), 1)
											insidedict["orf_end"] = self.extract_nth_bar(orfInfo.decode(), 2)
											insidedict["orf_from"] = orffrom.decode()
											insidedict["model_name"] = json_data[modelID]["model_name"]
											insidedict["model_type"] = json_data[modelID]["model_type"]
											insidedict["model_type_id"] = modelTypeID
											insidedict["model_id"] = modelID
											insidedict["pass_evalue"] = pass_evalue
											insidedict["pass_bitscore"] = pass_bitscore
											insidedict["ARO_accession"] = json_data[modelID]["ARO_accession"]
											insidedict["ARO_name"] = json_data[modelID]["ARO_name"]
											insidedict["ARO_category"] = json_data[modelID]["ARO_category"]
											insidedict["evalue"] = hsp.expect
											insidedict["bit_score"] = hsp.bits
											insidedict["max_identities"] = hsp.identities
											insidedict["cvterm_id"] = json_data[modelID]["model_sequences"]["sequence"][seqinModel]["NCBI_taxonomy"]["NCBI_taxonomy_cvterm_id"]
											insidedict["query"] = hsp.query
											insidedict["match"] = hsp.match
											insidedict["sequence_from_db"] = hsp.sbjct
											insidedict["sequence_from_broadstreet"] = json_data[modelID]["model_sequences"]["sequence"][seqinModel]["protein_sequence"]["sequence"]
											insidedict["dna_sequence_from_broadstreet"] = json_data[modelID]["model_sequences"]["sequence"][seqinModel]["dna_sequence"]["sequence"]
											if "partial" in json_data[modelID]["model_sequences"]["sequence"][seqinModel]["dna_sequence"].keys():
												insidedict["partial"] = json_data[modelID]["model_sequences"]["sequence"][seqinModel]["dna_sequence"]["partial"]
											else:
												insidedict["partial"] = "0"

											if self.input_type == 'contig':
												insidedict["query_start"] = self.extract_nth_hash(orfInfo.decode(), 1) + (hsp.query_start - 1)*3
												insidedict["query_end"] = self.extract_nth_hash(orfInfo.decode(), 1) + (hsp.query_start - 1)*3 + realQueryLength*3 - 1
												insidedict["orf_strand"] = self.extract_nth_hash(orfInfo.decode(), 3)
												insidedict["orf_start"] = self.extract_nth_hash(orfInfo.decode(), 1)
												insidedict["orf_end"] = self.extract_nth_hash(orfInfo.decode(), 2)
												insidedict["orf_from"] = self.extract_nth_hash(orfInfo.decode(), 0).rstrip()
												insidedict["hit_start"] = (hsp.sbjct_start-1)*3
												insidedict["hit_end"] = (hsp.sbjct_end)*3

												if orfInfo.decode().split(' # ')[0] in predicted_genes_dict:
													insidedict["orf_dna_sequence"] = predicted_genes_dict[orfInfo.decode().split(' # ')[0]]
													insidedict["orf_prot_sequence"] = str(Seq(predicted_genes_dict[orfInfo.decode().split(' # ')[0]]).translate(table=11)).strip("*")
													# insidedict["orf_prot_sequence"] = orf_protein_sequence
												else:
													insidedict["orf_dna_sequence"] = ""
													insidedict["orf_prot_sequence"] = ""

											elif self.input_type == 'protein':
												insidedict["query_start"] = hsp.query_start
												insidedict["query_end"] = hsp.query_start + realQueryLength
												insidedict["query_from"] = blast_record.query
												insidedict["orf_prot_sequence"] = orf_protein_sequence
												insidedict["hit_start"] = ""
												insidedict["hit_end"] = ""

											elif self.input_type == 'read':
												pass

											insidedict["perc_identity"] = float(format(float(insidedict["max_identities"]*100) / len(insidedict["query"]),'.2f'))
											strict["{}|hsp_num:{}".format(hitid.decode(),init)] = insidedict
											init += 1


								else:
									"""Loose hits."""
									# logger.debug("Loose hits")
									linsidedict = {}
									linsidedict["type_match"] = "Loose"
									linsidedict["orf_strand"] = self.extract_nth_bar(orfInfo.decode(), 0)
									linsidedict["orf_start"] = self.extract_nth_bar(orfInfo.decode(), 1)
									linsidedict["orf_end"] = self.extract_nth_bar(orfInfo.decode(), 2)
									linsidedict["orf_from"] = orffrom.decode().strip()
									linsidedict["model_name"] = json_data[modelID]["model_name"]
									linsidedict["model_type"] = json_data[modelID]["model_type"]
									linsidedict["model_type_id"] = modelTypeID
									linsidedict["pass_evalue"] = pass_evalue
									linsidedict["pass_bitscore"] = pass_bitscore
									linsidedict["model_id"] = modelID
									linsidedict["ARO_accession"] = json_data[modelID]["ARO_accession"]
									linsidedict["ARO_name"] = json_data[modelID]["ARO_name"]
									linsidedict["ARO_category"] = json_data[modelID]["ARO_category"]
									linsidedict["evalue"] = hsp.expect
									linsidedict["max_identities"] = hsp.identities
									linsidedict["bit_score"] = hsp.bits
									linsidedict["cvterm_id"] = json_data[modelID]["model_sequences"]["sequence"][seqinModel]["NCBI_taxonomy"]["NCBI_taxonomy_cvterm_id"]
									linsidedict["query"] = hsp.query
									linsidedict["match"] = hsp.match
									linsidedict["sequence_from_db"] = hsp.sbjct
									linsidedict["sequence_from_broadstreet"] = json_data[modelID]["model_sequences"]["sequence"][seqinModel]["protein_sequence"]["sequence"]
									linsidedict["dna_sequence_from_broadstreet"] = json_data[modelID]["model_sequences"]["sequence"][seqinModel]["dna_sequence"]["sequence"]
									if "partial" in json_data[modelID]["model_sequences"]["sequence"][seqinModel]["dna_sequence"].keys():
										linsidedict["partial"] = json_data[modelID]["model_sequences"]["sequence"][seqinModel]["dna_sequence"]["partial"]
									else:
										linsidedict["partial"] = "0"

									if self.input_type == 'contig':
										linsidedict["query_start"] = self.extract_nth_hash(orfInfo.decode(), 1) + (hsp.query_start - 1)*3
										linsidedict["query_end"] = self.extract_nth_hash(orfInfo.decode(), 1) + (hsp.query_start - 1)*3 + realQueryLength*3 - 1
										linsidedict["orf_strand"] = self.extract_nth_hash(orfInfo.decode(), 3)
										linsidedict["orf_start"] = self.extract_nth_hash(orfInfo.decode(), 1)
										linsidedict["orf_end"] = self.extract_nth_hash(orfInfo.decode(), 2)
										linsidedict["orf_from"] = self.extract_nth_hash(orfInfo.decode(), 0)
										linsidedict["hit_start"] = (hsp.sbjct_start-1)*3
										linsidedict["hit_end"] = (hsp.sbjct_end)*3

										if orfInfo.decode().split(' # ')[0] in predicted_genes_dict:
											linsidedict["orf_dna_sequence"] = predicted_genes_dict[orfInfo.decode().split(' # ')[0]]
											linsidedict["orf_prot_sequence"] = str(Seq(predicted_genes_dict[orfInfo.decode().split(' # ')[0]]).translate(table=11)).strip("*")
											# linsidedict["orf_prot_sequence"] = orf_protein_sequence
										else:
											linsidedict["orf_dna_sequence"] = ""
											linsidedict["orf_prot_sequence"] = ""

									elif self.input_type == 'protein':
										linsidedict["query_start"] = hsp.query_start
										linsidedict["query_end"] = hsp.query_start + realQueryLength
										linsidedict["query_from"] = blast_record.query
										linsidedict["orf_prot_sequence"] = orf_protein_sequence
										linsidedict["hit_start"] = ""
										linsidedict["hit_end"] = ""

									elif self.input_type == 'read':
										pass

									linsidedict["perc_identity"] = float(format(float(linsidedict["max_identities"]*100) / len(linsidedict["query"]), '.2f'))
									loose["{}|hsp_num:{}".format(hitid.decode(),init)] = linsidedict

									init += 1
							except Exception as e:
								logger.warning("Exception : {} -> {} -> Model({})".format(type(e), e, modelID))
								logger.warning("{} ---> hsp.bits: {} {} ? {}".format(json_data[modelID]["model_name"],hsp.bits, type(hsp.bits), type(pass_bitscore)))

				blastResults = self.results(blastResults, blast_record.query, perfect, strict , loose, self.include_nudge)

			return blastResults
