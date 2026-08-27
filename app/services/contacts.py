from db.database import repository

class ContactService:
    def __init__(
        self,
        contact_provider=None
    ):
        """
        contact_provider: Instance of TavilyContactProvider (or similar)
        """
        self.contact_provider = contact_provider

    async def discover_contacts(self, person: dict, company_name: str):
        """
        Use the contact provider to find contact information for a person,
        and upsert the results into the DB.
        """
        if not self.contact_provider:
            return None
            
        name = person.get("name") or person.get("full_name")
        linkedin_url = person.get("linkedin_url")
        person_id = person.get("person_id")
        
        if not name or not person_id:
            return None

        try:
            result = await self.contact_provider.search_contact(
                name=name,
                company=company_name,
                linkedin_url=linkedin_url
            )
            
            # Upsert email if found
            if not isinstance(result, dict):
                return None

            contact_ids = {}

            email = result.get("email")
            if email:
                contact_ids["email"] = repository.upsert_contact_point(
                    person_id=person_id,
                    contact_type="email",
                    contact_value=email,
                    confidence=result.get("confidence", 0.0)
                )
                
            # Upsert phone if found
            phone = result.get("phone")
            if phone:
                contact_ids["phone"] = repository.upsert_contact_point(
                    person_id=person_id,
                    contact_type="phone",
                    contact_value=phone,
                    confidence=result.get("confidence", 0.0)
                )
                
            # Save and link evidence if available.
            evidence = result.get("evidence", [])
            for ev in evidence:
                url = ev.get("url")
                if url:
                    source_id = repository.upsert_web_source(url=url, source_type="contact_evidence")
                    contact_type = ev.get("contact_type")
                    contact_id = contact_ids.get(contact_type)
                    if not contact_id and contact_ids:
                        contact_id = next(iter(contact_ids.values()))
                    if source_id and contact_id:
                        repository.create_contact_evidence(
                            contact_id=contact_id,
                            source_id=source_id,
                            evidence_text=ev.get("text") or ev.get("evidence"),
                        )
                        
            return result
            
        except Exception as e:
            print(f"[CONTACT SERVICE] Failed to discover contacts for {name}: {e}")
            return None
